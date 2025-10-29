# 1) Girdi sayfası: TE hedefi ve Cn + TEmax uygunluk kontrolü
# 2) Grafik sayfası: Gömülü matplotlib Canvas üzerinde TE(i) eğrileri
#    (Cn+10, Cn, Cn-10, Cn-20). Y ekseni 0..1 aralığında sabit.

import math
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import numpy as np

# --- Matplotlib (gömülü tuval) ---
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# ------------------ PDF formülleri ------------------

def chi(i, Cn):
    """chi(i) = 0.75 * (1 - exp(-0.3 * Cn * i))"""
    return 0.75 * (1.0 - math.exp(-0.3 * Cn * i))


def rho(Cn):
    """rho(Cn) = 1.2/Cn + 0.04"""
    return 1.2 / Cn + 0.04


def TE_of(i, Cn):
    """TE(i) = (1 - i) * (1 - rho/chi)  (mu = chi varsayımı ile)"""
    c = chi(i, Cn)
    if c <= 1e-15:
        return float("-inf")
    return (1.0 - i) * (1.0 - rho(Cn) / c)


# --- TE_max'ı sayısal tarama ile bul ---
I_MIN, I_MAX = 1e-6, 0.90


def find_te_max(Cn, steps=4000):
    xs = np.linspace(I_MIN, I_MAX, steps)
    tes = np.array([TE_of(x, Cn) for x in xs])
    k = int(np.argmax(tes))
    return float(xs[k]), float(tes[k])


# ------------------ GUI ------------------


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TE → Slip (i) ve TE(i) Eğrileri (Gömülü Canvas)")
        self.geometry("980x720")
        self.minsize(900, 650)
        self.resizable(True, True)

        self.style_bad = "#ffd6d6"
        self.style_ok = "white"

        # Notebook (2 sayfa)
        self.nb = ttk.Notebook(self)
        self.page1 = ttk.Frame(self.nb)
        self.page2 = ttk.Frame(self.nb)
        self.nb.add(self.page1, text="1) Girdi")
        self.nb.add(self.page2, text="2) TE Grafiği")
        self.nb.pack(fill="both", expand=True)

        self._build_page1()
        self._build_page2()

        # Varsayılan: 2. sayfa kilitli
        self.nb.tab(1, state="disabled")

    # ------------------ 1. Sayfa ------------------
    def _build_page1(self):
        pad = {"padx": 10, "pady": 8}

        ttk.Label(self.page1, text="Hedef TE (0–1):").grid(row=0, column=0, sticky="e", **pad)
        self.te_var = tk.StringVar(value="0.60")
        self.te_entry = ttk.Entry(self.page1, width=12, textvariable=self.te_var)
        self.te_entry.grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(self.page1, text="Cn:").grid(row=1, column=0, sticky="e", **pad)
        self.cn_var = tk.StringVar(value="40")
        self.cn_entry = ttk.Entry(self.page1, width=12, textvariable=self.cn_var)
        self.cn_entry.grid(row=1, column=1, sticky="w", **pad)

        self.info_lbl = ttk.Label(
            self.page1,
            text="TEmax ve uygunluk durumunu görmek için 'Hesapla'ya basın."
        )
        self.info_lbl.grid(row=2, column=0, columnspan=3, sticky="w", **pad)

        self.calc_btn = ttk.Button(self.page1, text="Hesapla", command=self.on_calculate)
        self.calc_btn.grid(row=3, column=1, sticky="w", **pad)

        for col in range(3):
            self.page1.grid_columnconfigure(col, weight=1)

        # Kullanılan formüller ve semboller
        formulas_frame = ttk.LabelFrame(self.page1, text="Kullanılan formüller ve semboller")
        formulas_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=10, pady=(4, 10))
        formulas_frame.columnconfigure(0, weight=1)
        self.page1.grid_rowconfigure(4, weight=1)

        formulas_text = (
            "Wismer ve Luth Eşitlikleri (1974)\n"
            "\n"
            "Tekerlek yuvarlanma direnci katsayısı:\n"
            "  ρ = Fᵣ / W = 1.2 / Cₙ + 0.04\n"
            "Tekerlek çevre kuvveti katsayısı:\n"
            "  μ = Mₜ / (W·r) = 0.75 · (1 − e^(−0.3·Cₙ·i))\n"
            "Tekerlek çekiş kuvveti (traksiyon) katsayısı:\n"
            "  K = F_T / W = 0.75 · (1 − e^(−0.3·Cₙ·i)) · (1.2 / Cₙ + 0.04)\n"
            "Tekerlek katsayısı:\n"
            "  Cₙ = C_l · B · D / W\n"
            "\n"
            "Traktif verim (TE = çıktı / girdi):\n"
            "  TE = (F_T / W) / (Mₜ / (W·r)) = (1 − i) · (1 − ρ / χ)\n"
            "  χ = 0.75 · (1 − e^(−0.3·Cₙ·i)) (uygulamada μ = χ varsayılmıştır)\n"
            "\n"
            "Semboller:\n"
            "  i : Patinaj oranı\n"
            "  W : Tekerleğe etkiyen dikey yük\n"
            "  Fᵣ : Yuvarlanma direnci kuvveti\n"
            "  F_T : Çekiş kuvveti\n"
            "  Mₜ : Tekerlek çevre momenti\n"
            "  r : Tekerlek yarıçapı\n"
            "  Cₙ : Zemin taşıma kapasitesi katsayısı\n"
            "  C_l : Kaldırma katsayısı, B : Tekerlek genişliği, D : Tekerlek çapı\n"
            "  ρ : Yuvarlanma direnci katsayısı, μ : Çevre kuvveti katsayısı, χ : TE hesabında kullanılan katsayı\n"
        )

        formulas_box = scrolledtext.ScrolledText(
            formulas_frame,
            wrap=tk.WORD,
            height=15,
            font=("TkDefaultFont", 10),
        )
        formulas_box.insert("1.0", formulas_text)
        formulas_box.configure(state="disabled")
        formulas_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)

        self.te_var.trace_add("write", lambda *_: self._reset_info())
        self.cn_var.trace_add("write", lambda *_: self._reset_info())

    def _reset_info(self):
        self.info_lbl.config(text="TEmax ve uygunluk durumunu görmek için 'Hesapla'ya basın.")
        self.te_entry.configure(background=self.style_ok)
        self.nb.tab(1, state="disabled")

    def _parse_float(self, s):
        return float(s.strip().replace(",", "."))

    def on_calculate(self):
        try:
            TE_target = self._parse_float(self.te_var.get())
            Cn = self._parse_float(self.cn_var.get())
            if not (0.0 < TE_target < 1.0):
                raise ValueError("TE 0–1 aralığında olmalı.")
            if Cn <= 0:
                raise ValueError("Cn pozitif olmalı.")
        except Exception as e:
            self.te_entry.configure(background=self.style_bad)
            messagebox.showerror("Hata", f"Girdi hatası: {e}")
            self.nb.tab(1, state="disabled")
            return

        # Uygunluk (TE_target <= TE_max) kontrolü
        i_at_max, te_max = find_te_max(Cn)
        if TE_target > te_max + 1e-9:
            self.te_entry.configure(background=self.style_bad)
            self.info_lbl.config(
                text=f"UYARI: Hedef TE={TE_target:.3f} > TEmax≈{te_max:.3f} (i≈{i_at_max:.3f}). "
                f"Bu Cn için hedef TE fiziksel olarak ulaşılamaz."
            )
            self.nb.tab(1, state="disabled")
            return

        # Her şey uygunsa 2. sayfayı aç ve grafiği hazırla
        self.te_entry.configure(background=self.style_ok)
        self.info_lbl.config(
            text=f"Tamam: TEmax≈{te_max:.3f} (i≈{i_at_max:.3f}). "
            f"2. sayfadaki TE grafiği hazırlandı."
        )
        self.nb.tab(1, state="normal")
        self.nb.select(1)
        self.draw_te_plot(Cn)

    # ------------------ 2. Sayfa ------------------
    def _build_page2(self):
        pad = {"padx": 10, "pady": 6}

        header = ttk.Frame(self.page2)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="TE(i) – Patinaj (i) Eğrileri (Cn+10, Cn, Cn−10, Cn−20). "
            "Seçilen Cn kalın çizilir. Y-ekseni 0–1 sabit."
        ).pack(side="left", **pad)

        # Matplotlib Figure + Canvas
        self.fig = Figure(figsize=(8.8, 4.8), dpi=100)
        self.ax = self.fig.add_subplot(111)

        canvas_frame = ttk.Frame(self.page2)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=6)

        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        # (İsteğe bağlı) Navigasyon araç çubuğu
        self.toolbar = NavigationToolbar2Tk(self.canvas, canvas_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side="bottom", fill="x")

        # Alt bilgi
        bottom = ttk.Frame(self.page2)
        bottom.pack(fill="x")
        self.cn_echo = ttk.Label(bottom, text="Seçilen Cn: —")
        self.cn_echo.pack(side="left", **pad)

        ttk.Button(bottom, text="Grafiği Yenile", command=self.on_replot).pack(side="left", **pad)

        self.comment_lbl = ttk.Label(
            self.page2,
            text="Grafik yorumları hesaplama yapıldığında burada görünecek.",
            justify="left",
            anchor="w",
            wraplength=860,
        )
        self.comment_lbl.pack(fill="x", padx=12, pady=(4, 12))

    def on_replot(self):
        try:
            Cn = self._parse_float(self.cn_var.get())
            if Cn <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Hata", "Geçerli bir Cn değeri giriniz.")
            return
        self.draw_te_plot(Cn)

    def draw_te_plot(self, Cn):
        """TE(i) eğrilerini gömülü tuvalde çizer. Y-ekseni 0..1."""
        self.cn_echo.config(text=f"Seçilen Cn: {Cn:g}")

        # Hazırla
        self.ax.clear()
        i_grid = np.linspace(0.0, 1.0, 800)

        # Cn listesi (≤0 olanları atla)
        cn_list = [Cn + 10, Cn, Cn - 10, Cn - 20]
        cn_list = [c for c in cn_list if c > 0]

        curve_maxima = {}
        for c in cn_list:
            y = np.array([TE_of(i, c) for i in i_grid])
            imax, temax = find_te_max(c)
            curve_maxima[c] = (imax, temax)
            if abs(c - Cn) < 1e-9:
                self.ax.plot(i_grid, y, linewidth=2.6, label=f"Cn = {c:g}")
                # Etiket: tepe civarına yerleştir
                self.ax.annotate(
                    f"Cn={c:g}",
                    xy=(imax, temax),
                    xytext=(min(0.85, imax + 0.08), min(0.95, temax + 0.08)),
                    arrowprops=dict(arrowstyle="->", lw=1.0),
                )
            else:
                self.ax.plot(i_grid, y, linewidth=1.4, label=f"Cn = {c:g}")

        # Eksenler ve sınırlar
        self.ax.set_xlabel("Patinaj i")
        self.ax.set_ylabel("TE")
        self.ax.set_title("TE(i) – Patinaj (i) Eğrileri (Gömülü)")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(0, 1.0)
        self.ax.set_ylim(0.0, 1.0)  # İstenen: y ekseni 0..1 sabit

        self.ax.legend(loc="lower right")
        self.fig.tight_layout()
        self.canvas.draw()

        comments = []
        primary_i_max, primary_te_max = curve_maxima.get(Cn, (float("nan"), float("nan")))
        if math.isfinite(primary_te_max):
            comments.append(
                f"• Seçilen Cn={Cn:g} için TEmax≈{primary_te_max:.3f} (i≈{primary_i_max:.3f})."
            )

        low_slip = TE_of(0.1, Cn)
        if math.isfinite(low_slip) and math.isfinite(primary_te_max):
            delta_low = primary_te_max - low_slip
            if delta_low > 0.05:
                comments.append(
                    f"• Düşük patinajda (i≈0.10) TE≈{low_slip:.3f}; optimuma göre {delta_low:.3f} birim artış potansiyeli bulunuyor."
                )
            else:
                comments.append(
                    f"• i≈0.10 seviyesinde TE≈{low_slip:.3f}; eğri optimum değere çok yakın ilerliyor."
                )

        high_slip = TE_of(0.6, Cn)
        if math.isfinite(high_slip):
            if high_slip < 0:
                comments.append(
                    f"• Yüksek patinajda (i≈0.60) TE≈{high_slip:.3f}; verim negatife düştüğü için enerji kaybı artıyor."
                )
            else:
                comments.append(
                    f"• i≈0.60 civarında TE≈{high_slip:.3f}; optimumdan uzaklaştıkça verim hızla azalıyor."
                )

        if len(curve_maxima) > 1:
            best_c, (best_i, best_te) = max(curve_maxima.items(), key=lambda item: item[1][1])
            if best_c != Cn:
                comments.append(
                    f"• Karşılaştırma: Cn={best_c:g} eğrisi TEmax≈{best_te:.3f} ile en yüksek verimi sunuyor (i≈{best_i:.3f})."
                )
            else:
                second = sorted(curve_maxima.items(), key=lambda item: item[1][1], reverse=True)[1]
                comments.append(
                    f"• Alternatif Cn={second[0]:g} için TEmax≈{second[1][1]:.3f}; seçilen Cn yine de daha avantajlı."
                )

        if len(comments) < 2:
            comments.append("• Grafik, Cn değerine bağlı TE değişimini kıyaslamaya yardımcı olur.")

        self.comment_lbl.config(text="\n".join(comments))


# ------------------ Çalıştır ------------------

if __name__ == "__main__":
    App().mainloop()
