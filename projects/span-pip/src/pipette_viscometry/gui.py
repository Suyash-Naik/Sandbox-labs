import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
import numpy as np
from .fitting import fit_span_data, FitResult
from .physics import calculate_viscosity, ViscoResults
from .config import Config

class FitState:
    def __init__(self, ax, color, title):
        self.ax = ax
        self.color = color
        self.title = title
        self.line = None
        self.fit: FitResult | None = None

    def update_fit(self, x: np.ndarray, y: np.ndarray, xmin: float, xmax: float):
        self.fit = fit_span_data(x, y, xmin, xmax)
        if self.line:
            self.line.remove()
        fit_x = np.array([self.fit.xmin, self.fit.xmax])
        fit_y = self.fit.slope * fit_x + self.fit.intercept
        self.line, = self.ax.plot(fit_x, fit_y, color=self.color, linewidth=2)


class InteractiveFitter:
    def __init__(self, x: np.ndarray, y: np.ndarray, filename: str, config: Config):
        self.x = x
        self.y = y
        self.filename = filename
        self.config = config
        self.skipped = False
        self.aborted = False

        self.fig, (self.ax_asp, self.ax_ret) = plt.subplots(2, 1, figsize=(10, 7))
        self.fig.canvas.manager.set_window_title(f"Pipette Viscometry — {filename}")
        plt.subplots_adjust(bottom=0.2, right=0.72)

        self.ax_asp.plot(x, y, 'b.', alpha=0.5, label="Raw Aspiration")
        self.ax_ret.plot(x, y, 'g.', alpha=0.5, label="Raw Retraction")

        self.asp_state = FitState(self.ax_asp, 'red', 'Aspiration')
        self.ret_state = FitState(self.ax_ret, 'purple', 'Retraction')

        self.span_asp = SpanSelector(
            self.ax_asp, lambda xmin, xmax: self._on_select(self.asp_state, xmin, xmax),
            'horizontal', useblit=True, props=dict(alpha=0.3, facecolor='yellow')
        )
        self.span_ret = SpanSelector(
            self.ax_ret, lambda xmin, xmax: self._on_select(self.ret_state, xmin, xmax),
            'horizontal', useblit=True, props=dict(alpha=0.3, facecolor='lightgreen')
        )

        self.info_ax = self.fig.add_axes([0.75, 0.2, 0.22, 0.65])
        self.info_ax.axis('off')
        self.info_text = self.info_ax.text(0, 0.9, "Select both spans...", transform=self.info_ax.transAxes, verticalalignment='top')

        # Control Buttons
        ax_done = self.fig.add_axes([0.45, 0.05, 0.12, 0.075])
        ax_skip = self.fig.add_axes([0.60, 0.05, 0.12, 0.075])
        
        self.btn_done = Button(ax_done, 'Done')
        self.btn_skip = Button(ax_skip, 'Skip (X)')

        self.btn_done.on_clicked(self._on_done)
        self.btn_skip.on_clicked(self._on_skip)

        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)

    def _on_select(self, state: FitState, xmin: float, xmax: float):
        try:
            state.update_fit(self.x, self.y, xmin, xmax)
            self._update_live_display()
            self.fig.canvas.draw_idle()
        except ValueError:
            pass

    def _update_live_display(self):
        msg = []
        if self.asp_state.fit:
            msg.append(f"Aspiration (m):\n  {self.asp_state.fit.slope:.4e}")
        if self.ret_state.fit:
            msg.append(f"Retraction (m):\n  {self.ret_state.fit.slope:.4e}")

        if self.asp_state.fit and self.ret_state.fit:
            try:
                res = calculate_viscosity(
                    self.asp_state.fit.slope,
                    self.ret_state.fit.slope,
                    self.config.instrument.Rp,
                    self.config.instrument.P_default,
                    self.config.instrument.Rcac
                )
                msg.append(f"\n--- Live Derived ---\nη: {res.eta:.3f}\nPc: {res.Pc:.3f}\nγ: {res.gamma:.3f}")
            except ValueError as e:
                msg.append(f"\nError: {e}")

        self.info_text.set_text("\n\n".join(msg))

    def _on_done(self, event):
        if not self.asp_state.fit or not self.ret_state.fit:
            self.info_text.set_text("Error: Must select\nBOTH spans first!")
            self.fig.canvas.draw_idle()
            return
        plt.close(self.fig)

    def _on_skip(self, event):
        self.skipped = True
        plt.close(self.fig)

    def _on_key_press(self, event):
        if event.key in ('x', 'X'):
            self._on_skip(event)
        elif event.key == 'escape':
            self.aborted = True
            plt.close(self.fig)

    def show(self) -> tuple[bool, bool, ViscoResults | None, FitResult | None, FitResult | None]:
        plt.show()
        if self.skipped or self.aborted or not (self.asp_state.fit and self.ret_state.fit):
            return self.skipped, self.aborted, None, self.asp_state.fit, self.ret_state.fit

        results = calculate_viscosity(
            self.asp_state.fit.slope,
            self.ret_state.fit.slope,
            self.config.instrument.Rp,
            self.config.instrument.P_default,
            self.config.instrument.Rcac
        )
        return False, False, results, self.asp_state.fit, self.ret_state.fit