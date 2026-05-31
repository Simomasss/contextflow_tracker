# ContextFlow ⏱️

ContextFlow je plně pasivní time-tracker pro Windows, který vám vrací čas strávený administrativou. Na rozdíl od běžných nástrojů vás nenutí k žádné interakci. Aplikace běží neinvazivně na pozadí, sleduje aktivní okna a na základě vaší lokální struktury složek autonomně přiřazuje čas konkrétním projektům.  Tato aplikace vznikla jako praktická část bakalářské práce zaměřené na eliminaci kognitivní zátěže znalostních pracovníků. 

## ⚠️ Stav projektu (MVP)
Aplikace je momentálně ve fázi **funkčního MVP**. Nejedná se o pouhý „proof of concept“, ale o technologický základ pro systém, který administraci měření času zcela eliminuje. Jako každý raný vývoj však obsahuje chyby a postrádá některé pokročilé funkce.

## Proč ContextFlow?
Vetšina stávajících nástrojů na trhu vyžadují pozornost od uživatele.
1. Manuální stopky neustále tříští vaše soustředění (flow).  
2. Automatické stopky vás po práci nutí k únavnému ručnímu třídění chaotických dat.

ContextFlow chce tuhle mezeru na trhu zaplnit plně pasivní aplikací, která načasuje veškerý odpracovaný čas pro účely fakturace a nebude vyžadovat žádnou interakci.

## 🚀 Upozornění pro uživatele (.exe verze)
Zatím Contextflow funguje jen na Windows, ale pracuje se na rozšíření.

Pokud jste si stáhli samotný `.exe` soubor, stačí ho jednoduše spustit. 

Aplikace si při startu automaticky vytvoří potřebné konfigurační soubory, logy a lokální SQLite databázi ve vašem uživatelském profilu (ve složce `AppData/Local/ContextFlowTracker`). Zároveň je původní `.exe` soubor na svém místě nahrazen zástupcem, takže se nemusíte starat o jeho manuální přesouvání.

## 🛠️ Sestavení aplikace (Pro vývojáře)
Pokud máte stažené zdrojové kódy a chcete si z nich vytvořit spustitelný `.exe` soubor sami, postupujte takto:

1. Nainstalujte potřebné závislosti z `requirements.txt`:
   ```cmd
   pip install -r requirements.txt
   ```

2. Ke zkompilování aplikace použijte nástroj `pyinstaller` s následujícími parametry:
   ```cmd
   pyinstaller --noconsole --onefile --name "ContextFlow_v0.1.8" --icon="src/gui/assets/icon.ico" --add-data "src;src" --collect-submodules customtkinter launcher.py
   ```

Výsledný spustitelný soubor najdete ve složce `dist/`.