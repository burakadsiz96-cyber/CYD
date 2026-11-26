# KADRAN — CYD 2.8" için cep saati esintili el enstrümanı kasası

ESP32-2432S028R (CYD 2.8") için tasarlandı. Ekran, dakika ölçekli yüzer bir kadranın içinde duruyor.
Cihaz cebe, anahtarlığa ve masaya göre düşünüldü.

| Saat parçası | Kadran'daki işlevi |
|---|---|
| Kadran ve dakika ölçeği | Ekran çerçevesi. Ölçek çizgileri panelde boydan boya yarık; arkadaki koyu boşluk onları boyar, tek renk baskıyla iki renkli görünür |
| Saat 12 işareti | Şeffaf kırmızı üçgen kakma |
| Kurma kolu (sağ alt, saat 4 yönünde) | Dokunmatik kalemin başlığı. Çekince kalem kasanın içindeki tünelden çıkar |
| Cep saati kulpu (tepe) | Anahtarlık deliği. Cihaz ortadan, dengeli asılır |
| Kronograf iticisi (sağ, saat 2 yönünde) | Açma/kapama düğmesi |
| Arkadaki dişli çark | Döner ayak ve parmak halkası (aşağıda) |
| Yakut taşlar | Vida başlarını ve çark merkezini örten şeffaf kırmızı kapaklar |
| Cenevre dalgaları | Arka yüz dokusu. Havalandırma yarıkları aynı dalgaların devamıdır |

## Çark ayak

- Çarkın dişli halkası menteşeden açılır. Masada ayak, elde parmak halkası olur.
- Çark merkez vidası etrafında döner, iki tırnak konumu vardır: **yatay** ve **dikey**. Arkadaki iki küçük
  simge ve ok, menteşenin hangi konumda olacağını gösterir.
- Halka yalnızca bu iki konumda açılır. Açıkken çark dönmez, çünkü halkanın kuyruğu sığ cebine oturur ve
  37°'de durur.
- Bu açıyla cihaz yatayda da dikeyde de dikeyden **23°** geriye yaslanarak durur (model içinde çözüldü).

## Parçalar ve renkler

Dosyalar `kadran_cikti/` klasöründe, **baskı yönünde** (STL + 3MF). Montaj: `kadran_montaj.step`.

| Dosya | Adet | Renk ("Orman" paleti) | Not |
|---|---|---|---|
| `on_kasa` | 1 | koyu yeşil | Yüzü tablada; destek gerekmez |
| `panel` | 1 | beyaz | Yüzü tablada; ölçek yarıkları boydan boya |
| `arka_kapak` | 1 | koyu yeşil | Sırtı tablada; gravür ve havalandırma ilk katmanlarda |
| `cark_gobek` | 1 | sarı | Üst yüzü tablada |
| `cark_halka` | 1 | sarı | Düz basılır |
| `kurma_kolu` | 1 | sarı | Dış yüzü tablada, kalem yuvası yukarıda |
| `itici` | 1 | sarı | |
| `yakut_x3` | 3 | **transparan kırmızı** | Yan vidaların kapakları |
| `yakut_merkez` | 1 | **transparan kırmızı** | Çark merkez kapağı |
| `pip` | 1 | **transparan kırmızı** | 12 işareti |
| `burc` | 1 | herhangi | Çarkın döndüğü burç (yerine M3 ara parça da olur) |

Diğer paletler (render'larda): **Gece** siyah + kırmızı, **Çelik** gri + sarı, **Eflatun** eflatun + turkuaz.
Yakutlar her palette transparan kırmızı.

Baskı: PETG veya PLA, 0,4 nozul, 0,2 mm katman (yakut, pip ve kurma kolu için 0,12 mm), 3 duvar,
%15–20 dolgu, destek yok. Bütün parçalar text-to-cad FDM baskı kontrolünden geçti (hata yok; uyarılar küçük
köprüler ve boşluklar). Bu kontroller genel tasarım kuralları; kendi yazıcının toleransı için önce küçük
parçaları dene.

## Donanım

- 3× M3×12 (yan vidalar, üstlerine yakut)
- 1× M3×16 (çarkın altında gizli kalan vida; kart deliğinden geçer)
- 1× M3×8 bombe başlı (ISO 7380) + 1× M3 pul Ø7 (çark mili)
- 19 mm 1,75 mm filament parçası (halka menteşe pimi)
- LiPo 503450 (5×34×50 mm, ~1000 mAh, korumalı)
- TP4056 USB-C şarj modülü (korumalı, ~28×17 mm); USB-C girişi üst yüzde
- 7×7 mm kilitli basmalı anahtar (itici)
- İsteğe bağlı: küçük 5 V yükseltici. CYD'nin 5 V girişi 3,7–4,2 V'ta 3,3 V regülatörü sınırda çalıştırır.
  Arka kapağın sol üst iç köşesinde ~20×20 mm boş yer var.

## Montaj

1. `pip`'i panelin 12 yuvasına önden bastır (gerekirse bir damla yapıştırıcı). Paneli ön kasanın yuvasına
   oturt; arkasındaki 4 pim raftaki deliklere girer.
2. CYD'yi ekranı aşağı bakacak şekilde ön kasaya yerleştir. LCD cebine oturur, kart deliklerine pimler girer.
3. Arka kapakta:
   - pili köşe tırnaklarının arasına çift taraflı bantla yapıştır;
   - TP4056'yı raylara USB-C üstte olacak şekilde yerleştir;
   - anahtarı yatağına yerleştir (yapıştır).
   Kablolama: pil → TP4056 B+/B−, TP4056 OUT+ → anahtar → CYD'nin 5 V (P1 konnektörü), OUT− → GND.
4. Kapağı kapat; dil kabukları hizalar. M3×16'yı çark bölgesindeki gizli delikten, 3× M3×12'yi yanlardan tak.
5. Çark:
   - burcu yuvasına, göbeği üstüne koy (tırnak yatay çukura otursun);
   - pulu ve M3×8'i tak, merkez yakutu bastır;
   - halkayı göbeğin etrafına yerleştir, 1,75 mm filament pimi halka + menteşe dilinden geçir ve kenarda kes.
6. 3 yakutu yan vida yuvalarına, itici başlığını anahtarın miline bastır.
7. Kurma kolunu kalemin arka ucuna bastır; kalemi sağ alttan tünele it.

## Ölç ve düzelt (parametreler, `kadran.py`'nin başında)

Kart ve kalem ölçüleri internetteki tutarsız kaynaklardan alındı. Baskıdan önce kumpasla kontrol et:

| Parametre | Varsayılan | Ne |
|---|---|---|
| `delik_araligi_x/y` | 78 × 42 mm | Kartın montaj delikleri arası |
| `ekran_kaydirma_x` | 0 | LCD'nin karta göre yatay kayması |
| `usb_y` | 0 | Sağ kenardaki USB'nin merkezi (yukarı +) |
| `sd_y` | 0 | Sol kenardaki microSD'nin merkezi |
| `kalem_cap` / `kalem_boy` | 5 / 87 mm | Benzer bir 2,8" ESP32 ekranın kalemi; seninkini ölç |
| `ayak_acisi` | 37° | Halkanın durdurağı; artırırsan cihaz daha çok yaslanır |

Değiştirip `cad run kadran.py` çalıştır, sonra çıktıları yeniden dışa aktar.
