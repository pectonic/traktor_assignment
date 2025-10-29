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

def chi_degeri(patinaj_orani, cn_degeri):
    """chi(i) = 0.75 * (1 - exp(-0.3 * Cn * i))"""
    return 0.75 * (1.0 - math.exp(-0.3 * cn_degeri * patinaj_orani))


def ro_degeri(cn_degeri):
    """rho(Cn) = 1.2/Cn + 0.04"""
    return 1.2 / cn_degeri + 0.04


def te_degeri(patinaj_orani, cn_degeri):
    """TE(i) = (1 - i) * (1 - rho/chi)  (mu = chi varsayımı ile)"""
    chi_sonuclari = chi_degeri(patinaj_orani, cn_degeri)
    if chi_sonuclari <= 1e-15:
        return float("-inf")
    return (1.0 - patinaj_orani) * (1.0 - ro_degeri(cn_degeri) / chi_sonuclari)


# --- TE_max'ı sayısal tarama ile bul ---
I_EN_AZ, I_EN_COK = 1e-6, 0.90


def te_maksimumunu_bul(cn_degeri, adim_sayisi=4000):
    patinaj_dizisi = np.linspace(I_EN_AZ, I_EN_COK, adim_sayisi)
    te_degerleri = np.array([te_degeri(patinaj, cn_degeri) for patinaj in patinaj_dizisi])
    en_yuksek_indis = int(np.argmax(te_degerleri))
    return float(patinaj_dizisi[en_yuksek_indis]), float(te_degerleri[en_yuksek_indis])


# ------------------ GUI ------------------


class Uygulama(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TE → Slip (i) ve TE(i) Eğrileri (Gömülü Canvas)")
        self.geometry("980x720")
        self.minsize(900, 650)
        self.resizable(True, True)

        self.stil_kotu = "#ffd6d6"
        self.stil_iyi = "white"

        # Notebook (2 sayfa)
        self.defter = ttk.Notebook(self)
        self.sayfa1 = ttk.Frame(self.defter)
        self.sayfa2 = ttk.Frame(self.defter)
        self.defter.add(self.sayfa1, text="1) Girdi")
        self.defter.add(self.sayfa2, text="2) TE Grafiği")
        self.defter.pack(fill="both", expand=True)

        self._sayfa1_olustur()
        self._sayfa2_olustur()

        # Varsayılan: 2. sayfa kilitli
        self.defter.tab(1, state="disabled")

    # ------------------ 1. Sayfa ------------------
    def _sayfa1_olustur(self):
        bosluk = {"padx": 10, "pady": 8}

        ttk.Label(self.sayfa1, text="Hedef TE (0–1):").grid(row=0, column=0, sticky="e", **bosluk)
        self.te_degiskeni = tk.StringVar(value="0.60")
        self.te_girdisi = ttk.Entry(self.sayfa1, width=12, textvariable=self.te_degiskeni)
        self.te_girdisi.grid(row=0, column=1, sticky="w", **bosluk)

        ttk.Label(self.sayfa1, text="Cn:").grid(row=1, column=0, sticky="e", **bosluk)
        self.cn_degiskeni = tk.StringVar(value="40")
        self.cn_girdisi = ttk.Entry(self.sayfa1, width=12, textvariable=self.cn_degiskeni)
        self.cn_girdisi.grid(row=1, column=1, sticky="w", **bosluk)

        self.bilgi_etiketi = ttk.Label(
            self.sayfa1,
            text="TEmax ve uygunluk durumunu görmek için 'Hesapla'ya basın."
        )
        self.bilgi_etiketi.grid(row=2, column=0, columnspan=3, sticky="w", **bosluk)

        self.hesapla_butonu = ttk.Button(self.sayfa1, text="Hesapla", command=self.hesapla)
        self.hesapla_butonu.grid(row=3, column=1, sticky="w", **bosluk)

        for sutun in range(3):
            self.sayfa1.grid_columnconfigure(sutun, weight=1)

        # Kullanılan formüller ve semboller
        formuller_cercevesi = ttk.LabelFrame(self.sayfa1, text="Kullanılan formüller ve semboller")
        formuller_cercevesi.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=10, pady=(4, 10))
        formuller_cercevesi.columnconfigure(0, weight=1)
        self.sayfa1.grid_rowconfigure(4, weight=1)

        formuller_metni = (
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

        formuller_kutusu = scrolledtext.ScrolledText(
            formuller_cercevesi,
            wrap=tk.WORD,
            height=15,
            font=("TkDefaultFont", 10),
        )
        formuller_kutusu.insert("1.0", formuller_metni)
        formuller_kutusu.configure(state="disabled")
        formuller_kutusu.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)

        self.te_degiskeni.trace_add("write", lambda *_: self._bilgi_sifirla())
        self.cn_degiskeni.trace_add("write", lambda *_: self._bilgi_sifirla())

    def _bilgi_sifirla(self):
        self.bilgi_etiketi.config(text="TEmax ve uygunluk durumunu görmek için 'Hesapla'ya basın.")
        self.te_girdisi.configure(background=self.stil_iyi)
        self.defter.tab(1, state="disabled")

    def _ondalik_coz(self, metin):
        return float(metin.strip().replace(",", "."))

    def hesapla(self):
        try:
            te_hedefi = self._ondalik_coz(self.te_degiskeni.get())
            cn_degeri = self._ondalik_coz(self.cn_degiskeni.get())
            if not (0.0 < te_hedefi < 1.0):
                raise ValueError("TE 0–1 aralığında olmalı.")
            if cn_degeri <= 0:
                raise ValueError("Cn pozitif olmalı.")
        except Exception as e:
            self.te_girdisi.configure(background=self.stil_kotu)
            messagebox.showerror("Hata", f"Girdi hatası: {e}")
            self.defter.tab(1, state="disabled")
            return

        # Uygunluk (TE_target <= TE_max) kontrolü
        patinaj_tepesinde, te_maksimumu = te_maksimumunu_bul(cn_degeri)
        if te_hedefi > te_maksimumu + 1e-9:
            self.te_girdisi.configure(background=self.stil_kotu)
            self.bilgi_etiketi.config(
                text=f"UYARI: Hedef TE={te_hedefi:.3f} > TEmax≈{te_maksimumu:.3f} (i≈{patinaj_tepesinde:.3f}). "
                f"Bu Cn için hedef TE fiziksel olarak ulaşılamaz."
            )
            self.defter.tab(1, state="disabled")
            return

        # Her şey uygunsa 2. sayfayı aç ve grafiği hazırla
        self.te_girdisi.configure(background=self.stil_iyi)
        self.bilgi_etiketi.config(
            text=f"Tamam: TEmax≈{te_maksimumu:.3f} (i≈{patinaj_tepesinde:.3f}). "
            f"2. sayfadaki TE grafiği hazırlandı."
        )
        self.defter.tab(1, state="normal")
        self.defter.select(1)
        self.te_grafigi_ciz(cn_degeri)

    # ------------------ 2. Sayfa ------------------
    def _sayfa2_olustur(self):
        bosluk = {"padx": 10, "pady": 6}

        ust_cerceve = ttk.Frame(self.sayfa2)
        ust_cerceve.pack(fill="x")

        ttk.Label(
            ust_cerceve,
            text="TE(i) – Patinaj (i) Eğrileri (Cn+10, Cn, Cn−10, Cn−20). "
            "Seçilen Cn kalın çizilir. Y-ekseni 0–1 sabit."
        ).pack(side="left", **bosluk)

        # Matplotlib Figure + Canvas
        self.sekil = Figure(figsize=(8.8, 4.8), dpi=100)
        self.eksen = self.sekil.add_subplot(111)

        tuval_cercevesi = ttk.Frame(self.sayfa2)
        tuval_cercevesi.pack(fill="both", expand=True, padx=10, pady=6)

        self.tuval = FigureCanvasTkAgg(self.sekil, master=tuval_cercevesi)
        self.tuval_arayuzu = self.tuval.get_tk_widget()
        self.tuval_arayuzu.pack(fill="both", expand=True)

        # (İsteğe bağlı) Navigasyon araç çubuğu
        self.arac_cubugu = NavigationToolbar2Tk(self.tuval, tuval_cercevesi, pack_toolbar=False)
        self.arac_cubugu.update()
        self.arac_cubugu.pack(side="bottom", fill="x")

        # Alt bilgi
        alt_cerceve = ttk.Frame(self.sayfa2)
        alt_cerceve.pack(fill="x")
        self.cn_etiketi = ttk.Label(alt_cerceve, text="Seçilen Cn: —")
        self.cn_etiketi.pack(side="left", **bosluk)

        ttk.Button(alt_cerceve, text="Grafiği Yenile", command=self.yeniden_ciz).pack(side="left", **bosluk)

        self.yorum_etiketi = ttk.Label(
            self.sayfa2,
            text="Grafik yorumları hesaplama yapıldığında burada görünecek.",
            justify="left",
            anchor="w",
            wraplength=860,
        )
        self.yorum_etiketi.pack(fill="x", padx=12, pady=(4, 12))

    def yeniden_ciz(self):
        try:
            cn_degeri = self._ondalik_coz(self.cn_degiskeni.get())
            if cn_degeri <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Hata", "Geçerli bir Cn değeri giriniz.")
            return
        self.te_grafigi_ciz(cn_degeri)

    def te_grafigi_ciz(self, cn_degeri):
        """TE(i) eğrilerini gömülü tuvalde çizer. Y-ekseni 0..1."""
        self.cn_etiketi.config(text=f"Seçilen Cn: {cn_degeri:g}")

        # Hazırla
        self.eksen.clear()
        patinaj_izgarasi = np.linspace(0.0, 1.0, 800)

        # Cn listesi (≤0 olanları atla)
        cn_listesi = [cn_degeri + 10, cn_degeri, cn_degeri - 10, cn_degeri - 20]
        cn_listesi = [cn_deger_satiri for cn_deger_satiri in cn_listesi if cn_deger_satiri > 0]

        egri_en_yuksekler = {}
        for cn_satiri in cn_listesi:
            te_egrisi_degerleri = np.array(
                [te_degeri(patinaj_orani, cn_satiri) for patinaj_orani in patinaj_izgarasi]
            )
            patinaj_tepe_noktasi, te_tepe_noktasi = te_maksimumunu_bul(cn_satiri)
            egri_en_yuksekler[cn_satiri] = (patinaj_tepe_noktasi, te_tepe_noktasi)
            if abs(cn_satiri - cn_degeri) < 1e-9:
                self.eksen.plot(
                    patinaj_izgarasi, te_egrisi_degerleri, linewidth=2.6, label=f"Cn = {cn_satiri:g}"
                )
                # Etiket: tepe civarına yerleştir
                self.eksen.annotate(
                    f"Cn={cn_satiri:g}",
                    xy=(patinaj_tepe_noktasi, te_tepe_noktasi),
                    xytext=(
                        min(0.85, patinaj_tepe_noktasi + 0.08),
                        min(0.95, te_tepe_noktasi + 0.08),
                    ),
                    arrowprops=dict(arrowstyle="->", lw=1.0),
                )
            else:
                self.eksen.plot(
                    patinaj_izgarasi, te_egrisi_degerleri, linewidth=1.4, label=f"Cn = {cn_satiri:g}"
                )

        # Eksenler ve sınırlar
        self.eksen.set_xlabel("Patinaj i")
        self.eksen.set_ylabel("TE")
        self.eksen.set_title("TE(i) – Patinaj (i) Eğrileri (Gömülü)")
        self.eksen.grid(True, alpha=0.3)
        self.eksen.set_xlim(0, 1.0)
        self.eksen.set_ylim(0.0, 1.0)  # İstenen: y ekseni 0..1 sabit

        self.eksen.legend(loc="lower right")
        self.sekil.tight_layout()
        self.tuval.draw()

        yorumlar = []
        birincil_patinaj_maks, birincil_te_maks = egri_en_yuksekler.get(
            cn_degeri, (float("nan"), float("nan"))
        )
        if math.isfinite(birincil_te_maks):
            yorumlar.append(
                f"• Seçilen Cn={cn_degeri:g} için TEmax≈{birincil_te_maks:.3f} (i≈{birincil_patinaj_maks:.3f})."
            )

        dusuk_patinaj_te = te_degeri(0.1, cn_degeri)
        if math.isfinite(dusuk_patinaj_te) and math.isfinite(birincil_te_maks):
            delta_dusuk = birincil_te_maks - dusuk_patinaj_te
            if delta_dusuk > 0.05:
                yorumlar.append(
                    f"• Düşük patinajda (i≈0.10) TE≈{dusuk_patinaj_te:.3f}; optimuma göre {delta_dusuk:.3f} birim artış potansiyeli bulunuyor."
                )
            else:
                yorumlar.append(
                    f"• i≈0.10 seviyesinde TE≈{dusuk_patinaj_te:.3f}; eğri optimum değere çok yakın ilerliyor."
                )

        yuksek_patinaj_te = te_degeri(0.6, cn_degeri)
        if math.isfinite(yuksek_patinaj_te):
            if yuksek_patinaj_te < 0:
                yorumlar.append(
                    f"• Yüksek patinajda (i≈0.60) TE≈{yuksek_patinaj_te:.3f}; verim negatife düştüğü için enerji kaybı artıyor."
                )
            else:
                yorumlar.append(
                    f"• i≈0.60 civarında TE≈{yuksek_patinaj_te:.3f}; optimumdan uzaklaştıkça verim hızla azalıyor."
                )

        if len(egri_en_yuksekler) > 1:
            en_iyi_cn, (en_iyi_patinaj, en_iyi_te) = max(
                egri_en_yuksekler.items(), key=lambda item: item[1][1]
            )
            if en_iyi_cn != cn_degeri:
                yorumlar.append(
                    f"• Karşılaştırma: Cn={en_iyi_cn:g} eğrisi TEmax≈{en_iyi_te:.3f} ile en yüksek verimi sunuyor (i≈{en_iyi_patinaj:.3f})."
                )
            else:
                ikinci = sorted(
                    egri_en_yuksekler.items(), key=lambda item: item[1][1], reverse=True
                )[1]
                yorumlar.append(
                    f"• Alternatif Cn={ikinci[0]:g} için TEmax≈{ikinci[1][1]:.3f}; seçilen Cn yine de daha avantajlı."
                )

        if len(yorumlar) < 2:
            yorumlar.append("• Grafik, Cn değerine bağlı TE değişimini kıyaslamaya yardımcı olur.")

        self.yorum_etiketi.config(text="\n".join(yorumlar))


# ------------------ Çalıştır ------------------

if __name__ == "__main__":
    Uygulama().mainloop()
