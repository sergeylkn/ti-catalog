"""
Auto-generated parser stubs and configs based on manifest.txt

This file contains:
- manifest_filenames: list of PDF filenames from manifest
- base_url: derived base URL where PDFs are hosted
- generate_parsers_json(): generates parsers/parsers.json with default parser
  configurations for each PDF.
- make_parser_stub_for(filename): returns a string with a parser stub for that PDF

Note: This code does not perform PDF downloads or analysis here; it generates
parser templates and a parsers.json that you can later refine. To perform full
analysis, run the scripts/analyze_and_generate_parsers.py script in an
environment with network access and required dependencies.
"""
from pathlib import Path
import json
import re

BASE_URL = "https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev"

manifest_filenames = [
    "industrial_hoses_compensators.pdf",
    "industrial_hoses_floating_hoses_and_equipment.pdf",
    "industrial_hoses_heated_hoses.pdf",
    "industrial_hoses_hoses_for_braking_systems.pdf",
    "industrial_hoses_technical_gas.pdf",
    "ochystka-ta-zmyvannya_aksesuary-dlya-zmashchuvannya.pdf",
    "ochystka-ta-zmyvannya_nyzkonapirni-vodyani-pistolety.pdf",
    "ochystka-ta-zmyvannya_obpresovky-dlya-shlanhiv-ta-myyky.pdf",
    "ochystka-ta-zmyvannya_shlanhy-ta-tavotnytsi-maslonky-dlya-zmashchuvannya.pdf",
    "pneumatic_fittings.pdf",
    "pneumatic_hoses.pdf",
    "pneumatic_speedfit_system.pdf",
    "pretsyziyna-armatura_bloky-komplekty-klapaniv.pdf",
    "pretsyziyna-armatura_inshi-klapany-ta-filtry.pdf",
    "pretsyziyna-armatura_inshi-zyednuvachi.pdf",
    "pretsyziyna-armatura_manometry-ta-aksesuary.pdf",
    "pretsyziyna-armatura_pretsyziyna-armatura-zahalna-informatsiya.pdf",
    "pretsyziyna-armatura_pretsyziyni-holchasti-klapany.pdf",
    "pretsyziyna-armatura_pretsyziyni-kulovi-krany-klapany.pdf",
    "pretsyziyna-armatura_pretsyziyni-rizbovi-zyednuvachi.pdf",
    "pretsyziyna-armatura_pretsyziyni-shvydko-rozyemni-zyednuvachi.pdf",
    "pretsyziyna-armatura_pretsyziyni-truby.pdf",
    "pretsyziyna-armatura_pretsyziyni-zyednuvachi-let-lok.pdf",
    "promyslova-armatura_chavunni-zatyskni-oboymy-dlya-obtyskannya-fitynhiv.pdf",
    "promyslova-armatura_fitynhy-dlya-vnutrishnoho-obtyskannya.pdf",
    "promyslova-armatura_hammer-lug-zyednannya-ta-armatura.pdf",
    "promyslova-armatura_inshi-oboymy-khomuty-dlya-trub.pdf",
    "promyslova-armatura_inshi-zyednuvalni-elementy-dlya-vydobutku-nafty-ta-hazu.pdf",
    "promyslova-armatura_khomuty-dlya-fiksatsiyi-ta-montuvannya-kintsevykiv.pdf",
    "promyslova-armatura_khomuty-p-clip.pdf",
    "promyslova-armatura_kintsevyky-ta-zyednannya-typu-ec.pdf",
    "promyslova-armatura_kintsevyky-typu-cn.pdf",
    "promyslova-armatura_klykovi-zyednannya-40-mm.pdf",
    "promyslova-armatura_kulovi-krany.pdf",
    "promyslova-armatura_latunni-rizbovi-fitynhy.pdf",
    "promyslova-armatura_nerzhaviyuchi-hihiyenichni-klapany.pdf",
    "promyslova-armatura_oboymy-dlya-remontu-ta-zyednannya-trub.pdf",
    "promyslova-armatura_oboymy-shkaralupchasti-dlya-montuvannya-kintsevykiv.pdf",
    "promyslova-armatura_palyvni-zyednannya-na-skrutku.pdf",
    "promyslova-armatura_palyvni-zyednannya.pdf",
    "promyslova-armatura_peredavalni-transportuvalni-zyednannya-zahalna-informatsiya.pdf",
    "promyslova-armatura_perevantazhuvalni-ohlyadovi-lyuky.pdf",
    "promyslova-armatura_perevantazhuvalni-sharnirno-rukhomi-plechi.pdf",
    "promyslova-armatura_plastykovi-kintsevyky-ta-zyednuvachi.pdf",
    "promyslova-armatura_promyslovi-rizbovi-adaptery.pdf",
    "promyslova-armatura_promyslovi-rizbovi-zyednannya.pdf",
    "promyslova-armatura_rizbovi-armatury-z-chavunu-ta-stali.pdf",
    "promyslova-armatura_rozyemy-camlock-iz-zakhystom.pdf",
    "promyslova-armatura_rozyemy-camlock.pdf",
    "promyslova-armatura_rozyemy-ibc.pdf",
    "promyslova-armatura_shvydko-rozyemni-zyednannya-dlya-pres-form.pdf",
    "promyslova-armatura_shvydko-rozyemni-zyednannya-plastykovi-promyslovi.pdf",
    "promyslova-armatura_shvydko-rozyemy-nerzhaviyuchi-dlya-vody.pdf",
    "promyslova-armatura_shvydkorozyemni-zyednannya-dlya-kharchovoyi-promyslovosti.pdf",
    "promyslova-armatura_strichkova-zatyskna-systema.pdf",
    "promyslova-armatura_sukho-rozyemni-zyednannya.pdf",
    "promyslova-armatura_ushchilnennya-ta-kripylni-bolty-dlya-flantsevykh-zyednan.pdf",
    "promyslova-armatura_vazhilne-zyednannya-klaudia.pdf",
    "promyslova-armatura_vazhilni-zyednannya-anfor.pdf",
    "promyslova-armatura_vazhilni-zyednannya-bauer.pdf",
    "promyslova-armatura_vazhilni-zyednannya-ferrari.pdf",
    "promyslova-armatura_vazhilni-zyednannya-laux-42.pdf",
    "promyslova-armatura_vazhilni-zyednannya-perrot.pdf",
    "promyslova-armatura_vsmoktuvalni-filtry.pdf",
    "promyslova-armatura_zaliznychni-zyednuvachi.pdf",
    "promyslova-armatura_zalyvalni-zapravni-pistolety.pdf",
    "promyslova-armatura_zapravna-nalyvna-armatura-insha.pdf",
    "promyslova-armatura_zasuvky-zapirni-klapany.pdf",
    "promyslova-armatura_zvarni-truby-ta-fasonni-chastyny-pid-pryvarku.pdf",
    "promyslova-armatura_zvorotni-klapany-ta-filtry.pdf",
    "promyslova-armatura_zyednannya-dlya-nyzkoho-tysku-zahalnoho-pryznachennya.pdf",
    "promyslova-armatura_zyednannya-dlya-shtukaturky.pdf",
    "promyslova-armatura_zyednannya-gost.pdf",
    "promyslova-armatura_zyednannya-guillemin.pdf",
    "promyslova-armatura_zyednannya-klykove-sms.pdf",
    "promyslova-armatura_zyednannya-nor.pdf",
    "promyslova-armatura_zyednannya-rotta.pdf",
    "promyslova-armatura_zyednannya-storz.pdf",
    "promyslova-armatura_zyednannya-ta-lpglng-ta-kriohazy.pdf",
    "promyslova-armatura_zyednannya-tw.pdf",
    "promyslova-armatura_zyednuvachi-avariynoho-vidyednannya-avariyni-rozyemy.pdf",
    "promyslova-armatura_zyednuvachi-dlya-piskostrumynnoyi-obrobky.pdf",
    "promyslova-armatura_zyednuvachi-z-zatysknym-kiltsem.pdf",
    "promyslova-pnevmatyka_aksesuary-dlya-frl.pdf",
    "promyslova-pnevmatyka_frl-pidhotuvannya-povitrya.pdf",
    "promyslova-pnevmatyka_pnevmatychni-klapany-ta-aksesuary-do-nykh.pdf",
    "promyslova-pnevmatyka_rizbovi-latunni-zyednannya.pdf",
    "promyslova-pnevmatyka_rizbovi-zyednannya-zi-stali-marky-316.pdf",
    "promyslova-pnevmatyka_tsanhovi-funktsionalni-rozyemy.pdf",
    "promyslova-pnevmatyka_zyednannya-banjo.pdf",
    "promyslova-pnevmatyka_zyednannya-na-vrizne-kolechko.pdf",
    "promyslova-pnevmatyka_zyednannya-na-zatysknu-hayku.pdf",
    "prystroyi-ta-aksesuary_aksesuary-dlya-barabaniv.pdf",
    "prystroyi-ta-aksesuary_bahatofunktsionalne-obladnannya-dlya-obrobky-trub.pdf",
    "prystroyi-ta-aksesuary_barabany-ta-kotushky-oznayomcha-informatsiya.pdf",
    "prystroyi-ta-aksesuary_inshe-obladnannya.pdf",
    "prystroyi-ta-aksesuary_inshi-barabany.pdf",
    "prystroyi-ta-aksesuary_obladnannya-dlya-montuvannya-kiletsta-rozvaltsyuvannya.pdf",
    "prystroyi-ta-aksesuary_obladnannya-dlya-ochyshchennya-shlanhiv-i-trubok.pdf",
    "prystroyi-ta-aksesuary_pistolety-ta-obladnannya-dlya-pidkachky-kolis.pdf",
    "prystroyi-ta-aksesuary_pnevmatychni-pistolety-spetsialni.pdf",
    "prystroyi-ta-aksesuary_pnevmo-aksesuary.pdf",
    "prystroyi-ta-aksesuary_povitryani-pistolety.pdf",
    "prystroyi-ta-aksesuary_promyslova-khimiya.pdf",
    "prystroyi-ta-aksesuary_pruzhynno-zmotuval-ni-barabany.pdf",
    "prystroyi-ta-aksesuary_prystriy-dlya-hnuttya-trub.pdf",
    "prystroyi-ta-aksesuary_prystroyi-dlya-markuvannya.pdf",
    "prystroyi-ta-aksesuary_prystroyi-dlya-rizannya-shlanhiv.pdf",
    "prystroyi-ta-aksesuary_prystroyi-dlya-znimannya-vnutrishnoho.pdf",
    "prystroyi-ta-aksesuary_ruchni-hidravlichni-elektrychni-pnevmatychni-barabany.pdf",
    "prystroyi-ta-aksesuary_stiyky-dlya-shlanhiv.pdf",
    "prystroyi-ta-aksesuary_vysokotemperaturnyy-zakhyst.pdf",
    "prystroyi-ta-aksesuary_zakhyst.pdf",
    "prystroyi-ta-aksesuary_zakhysty.pdf",
    "prystroyi-ta-aksesuary_zatyskni-presy.pdf",
    "prystroyi-ta-aksesuary_znaryaddya-ta-instrumenty-dlya-vydalennya-zadyrok-na-trubakh.pdf",
    "shlanhy-dlya-promyslovosti_aksesuary-dlya-vodyanoyi-pary.pdf",
    "shlanhy-dlya-promyslovosti_avtomobilni-shlanhy-ta-zyednannya.pdf",
    "shlanhy-dlya-promyslovosti_fitynhy-dlya-systemy-kondytsionuvannya-povitrya.pdf",
    "shlanhy-dlya-promyslovosti_halmivni-fitynhy.pdf",
    "shlanhy-dlya-promyslovosti_kintsevyky-fitynhy-dlya-vodyanoyi-pary.pdf",
    "shlanhy-dlya-promyslovosti_kompozytni-shlanhy.pdf",
    "shlanhy-dlya-promyslovosti_kompozytni-zyednannya-dlya-shlanhiv.pdf",
    "shlanhy-dlya-promyslovosti_metalorukavy-napirni-ta-yikh-armatura-fitynhy.pdf",
    "shlanhy-dlya-promyslovosti_montazh-fitynhiv-dlya-kondytsioneriv.pdf",
    "shlanhy-dlya-promyslovosti_santekhnichni-shlanhy.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-dlya-kharchovykh-rechovyn.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-dlya-khimichnykh-rechovyn.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-dlya-naftoproduktiv.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-dlya-perekachuvannya-sypuchykh-rechovyn.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-dlya-system-kondytsionuvannya-povitrya.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-dlya-vody-ta-povitrya.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-dlya-vodyanoyi-pary.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-ta-liniyi-dlya-okholodzhuvalnoyi-ridyny.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-tygon.pdf",
    "shlanhy-dlya-promyslovosti_shlanhy-v-teflonovomu-obpletenni-ta-fitynhy-dlya-nykh.pdf",
    "shlanhy-dlya-promyslovosti_spiralni-stalevi-shlanhy.pdf",
    "shlanhy-dlya-promyslovosti_sylikonovi-promyslovi-shlanhy.pdf",
    "shlanhy-dlya-promyslovosti_teflonovi-rukavy-dlya-promyslovykh-protsesiv.pdf",
    "shlanhy-dlya-promyslovosti_teflonovi-shlanhy-bez-obpletennya.pdf",
    "shlanhy-dlya-promyslovosti_teflonovi-shlanhy-zahalnainformatsiya.pdf",
    "shlanhy-dlya-promyslovosti_universalni-samozatyskni-shlanhy.pdf",
    "shlanhy-dlya-promyslovosti_universalni-shlanhy.pdf",
    "shlanhy-dlya-promyslovosti_vytyazhni-ta-ventylyatsiyni-shlanhy.pdf",
    "shlanhy-dlya-promyslovosti_zyednuvachi-dlya-vytyazhnykh-shlanhiv.pdf",
    "sylova-hidravlika_adaptery-uhp.pdf",
    "sylova-hidravlika_droselni-ta-zapobizhni-klapany.pdf",
    "sylова-hidravлика_fitynhy-mp-hp.pdf",
    "sylова-hидravлика_fitynhy-ta-adaptery-stecko.pdf",
    "sylова-hидravлика_fitynhy-та-obtyskni-vtulky-typ-interlock-typ-il.pdf",
    "sylова-hидravлика_flantsevi-zyednannya-dlya-hidravличnykh-nasosiv.pdf",
    "sylова-hидravлика_flantsevi-zyednannya-sae.pdf",
    "sylова-hидravлика_hidravличni-adaptery.pdf",
    "sylова-hидravлика_hidravличni-ahrehaty.pdf",
    "sylова-hидravлика_hidravличni-klapany-klasyfikatsiya.pdf",
    "sylова-hидravлика_hidravличni-kulovi-krany.pdf",
    "sylова-hидravлика_hidravличni-nasosy.pdf",
]


def safe_name(fname: str) -> str:
    return re.sub(r"[^0-9a-zA-Z_]+", "_", fname)


def default_parser_config(fname: str) -> dict:
    """Return default parser config for filename.

    Since we don't analyze PDFs here, configs are conservative defaults and
    should be refined after actual PDF analysis.
    """
    return {
        "filename": fname,
        "url": f"{BASE_URL.rstrip('/')}/{fname}",
        "layout_type": "unknown",
        "scanned": None,
        "tables_found": None,
        "images_found": None,
        "recommended_parsers": {
            "text_extraction": "pymupdf or pdfplumber",
            "ocr": "pytesseract (if scanned)",
            "table_parser": "camelot or tabula (if tables)",
            "image_extraction": True,
            "segment_strategy": "card_segmentation_or_sectioning"
        },
        "regex_sku": r"[A-Z0-9\\-_/]{4,}",
        "regex_dimension": r"(\\\\d+(?:\\\\.\\\\d+)?)\\\\s*(mm|cm|m)",
        "regex_pressure": r"(\\\\d+(?:\\\\.\\\\d+)?)\\\\s*(bar|MPa)",
    }


def generate_parsers_json(target: str = None):
    out = Path(target or Path(__file__).parent / "parsers.json")
    configs = [default_parser_config(fn) for fn in manifest_filenames]
    out.write_text(json.dumps(configs, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)


if __name__ == '__main__':
    print("This module generates parser templates for each PDF listed in the manifest.")
    p = generate_parsers_json()
    print("Wrote:", p)
