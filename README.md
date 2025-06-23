# Perhe Kotityöapp

Mobiiliystävällinen verkkosovellus kotitöiden ja tehtävien hallintaan lapsille, rakennettu Python Flaskilla. Täydellinen perheille, joilla on 8-11-vuotiaita lapsia, jotka haluavat pelillistää kotitalouden vastuut.

## Ominaisuudet

### Vanhemmille
- ✅ Luo ja hallitse kotitalouden tehtäviä
- ✅ Aseta pistearvot ja vaikeustasot
- ✅ Lisää useita lasten tilejä
- ✅ Seuraa tehtävien valmistumista ja etenemistä
- ✅ Katso perheen tilastoja ja saavutuksia
- ✅ Mobiiliystävällinen käyttöliittymä

### Lapsille
- ✅ Selaa vapaana olevia tehtäviä
- ✅ Valitse tehtäviä työskentelyä varten
- ✅ Valmista tehtäviä ja ansaitse pisteitä
- ✅ Katso henkilökohtaisia saavutuksia ja etenemistä
- ✅ Yksinkertainen, lapsiystävällinen käyttöliittymä
- ✅ Pisteseuranta ja palkintojärjestelmä

## Nopea aloitus

### Edellytykset
- Python 3.7 tai uudempi
- pip (Python-paketin asennusohjelma)

### Asennus

1. **Kloonaa tai lataa projekti**
   ```bash
   git clone <repository-url>
   cd ChoresApp
   ```

2. **Asenna riippuvuudet**
   ```bash
   pip install -r requirements.txt
   ```

3. **Käynnistä sovellus**
   ```bash
   python app.py
   ```

4. **Käytä sovellusta**
   - Avaa selain ja mene osoitteeseen `http://localhost:8080`
   - Oletus vanhempi kirjautuminen:
     - Käyttäjänimi: `parent`
     - Salasana: `parent123`

## Lasten tilien asettaminen

1. **Kirjaudu vanhempana** oletustunnuksilla
2. **Siirry Lapset-välilehdelle** vanhempien hallintapaneelissa
3. **Klikkaa "Lisää lapsi"** luodaksesi tilejä lapsillesi
4. **Käytä yksinkertaisia käyttäjänimiä ja salasanoja** joita lapsesi muistavat
5. **Auta lapsiasi kirjautumaan** ensimmäisen kerran

## Tehtävien luominen

1. **Vanhempien hallintapaneelista** klikkaa "Uusi tehtävä" tai kelluvaa + -painiketta
2. **Täytä tehtävän tiedot**:
   - Otsikko (esim. "Siivoa keittiön pöytä")
   - Kuvaus (valinnainen)
   - Pisteet (5-100, vaikeustason mukaan)
   - Vaikeustaso (Helppo/Keskitaso/Vaikea)
   - Määräaika (valinnainen)
3. **Tallenna tehtävä** - se ilmestyy vapaana olevien tehtävien listaan

## Tehtävien vaikeustasojen ohjeet

- **Helppo (5-10 pistettä)**: Tee sänky, laita lelut pois, ruoki lemmikki, tyhjennä pöytä
- **Keskitaso (10-20 pistettä)**: Imuroi huone, lataa tiskikone, taittaa pyykki, kastella kasvit
- **Vaikea (20+ pistettä)**: Siivoa kylpyhuone, järjestä vaatekaappi, pese ikkunat, auta ruoanlaitossa

## Raspberry Pi -asennus

### Vaihtoehto 1: Manuaalinen asennus

1. **Asenna Python ja pip Raspberry Pi:lle**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **Kloonaa projekti**
   ```bash
   git clone <repository-url>
   cd ChoresApp
   ```

3. **Asenna riippuvuudet**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Käynnistä sovellus**
   ```bash
   python3 app.py
   ```

5. **Käytä muilta laitteilta**
   - Etsi Pi:n IP-osoite: `hostname -I`
   - Käytä mistä tahansa laitteesta verkossa: `http://[PI_IP_OSOITE]:8080`

### Vaihtoehto 2: Systemd-palvelu (Suositeltu)

1. **Luo systemd-palvelutiedosto**
   ```bash
   sudo nano /etc/systemd/system/chores-app.service
   ```

2. **Lisää seuraava sisältö** (muuta polut tarpeen mukaan):
   ```ini
   [Unit]
   Description=Perhe Kotityöapp
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/ChoresApp
   ExecStart=/usr/bin/python3 /home/pi/ChoresApp/app.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Ota palvelu käyttöön ja käynnistä se**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable chores-app
   sudo systemctl start chores-app
   ```

4. **Tarkista palvelun tila**
   ```bash
   sudo systemctl status chores-app
   ```

### Vaihtoehto 3: Gunicornin käyttö (Tuotanto)

1. **Asenna Gunicorn**
   ```bash
   pip3 install gunicorn
   ```

2. **Luo WSGI-tiedosto** (`wsgi.py`):
   ```python
   from app import app

   if __name__ == "__main__":
       app.run()
   ```

3. **Käytä Gunicornia**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8080 wsgi:app
   ```

## Tietoturva

- **Muuta oletus vanhempi salasana** ensimmäisen kirjautumisen jälkeen
- **Käytä vahvoja salasanoja** lasten tileille
- **Pidä sovellus vain paikallisverkossa**
- **Varmuuskopioi tietokanta** säännöllisesti (`chores.db`-tiedosto)
- **Päivitä salausavain** `app.py`-tiedostossa tuotantokäyttöä varten

## Tietokannan varmuuskopiointi

Sovellus käyttää SQLiteä yksinkertaisuuden vuoksi. Varmuuskopioidaksesi tietojasi:

```bash
# Kopioi tietokantatiedosto
cp chores.db chores_backup_$(date +%Y%m%d).db

# Tai käytä SQLite-varmuuskopiokomentoa
sqlite3 chores.db ".backup 'chores_backup_$(date +%Y%m%d).db'"
```

## Mukauttaminen

### Värien ja teeman muuttaminen
Muokkaa CSS-muuttujia `templates/base.html`-tiedostossa:
```css
:root {
    --primary-color: #4CAF50;
    --secondary-color: #2196F3;
    --accent-color: #FF9800;
    /* ... muut värit */
}
```

### Uusien ominaisuuksien lisääminen
Sovellus on rakennettu Flaskilla ja käyttää:
- **SQLAlchemy** tietokannan hallintaan
- **Bootstrap 5** responsiiviseen suunnitteluun
- **Font Awesome** kuvakkeisiin
- **SQLite** tietojen tallentamiseen

## Ongelmien ratkaisu

### Yleisiä ongelmia

1. **Portti 8080 on jo käytössä**
   ```bash
   # Etsi mikä käyttää porttia
   sudo lsof -i :8080
   # Pysäytä prosessi tai vaihda porttia app.py:ssä
   ```

2. **Käyttöoikeusvirheitä**
   ```bash
   # Varmista että sinulla on kirjoitusoikeudet
   chmod 755 /path/to/ChoresApp
   ```

3. **Tietokantavirheitä**
   ```bash
   # Poista tietokantatiedosto nollataksesi
   rm chores.db
   # Käynnistä sovellus uudelleen - se luo uuden tietokannan
   ```

### Lokit
Tarkista sovelluksen lokit:
```bash
# Jos käytät systemd:tä
sudo journalctl -u chores-app -f

# Jos ajat manuaalisesti, lokit näkyvät terminaalissa
```

## Tuki

Ongelmia tai kysymyksiä varten:
1. Tarkista yllä oleva ongelmien ratkaisu -osio
2. Varmista Python-versiosi (`python3 --version`)
3. Varmista että kaikki riippuvuudet on asennettu (`pip3 list`)
4. Tarkista sovelluksen lokit virheilmoituksia varten

## Lisenssi

Tämä projekti on avoimen lähdekoodin ja saatavilla MIT-lisenssillä.

---

**Hauskaa kotityöjen hallintaa! 🏠✨**