from collections import OrderedDict

grammar = OrderedDict(
    {
        "Telheader_Quelle": {
            "type": "str",
            "length": 10,
            "dp": False,
            "ubl_path": False,
            "df_val": False,
            "df_func": "get_source",
        },
        "Telheader_Ziel": {
            "type": "str",
            "length": 10,
            "dp": False,
            "ubl_path": False,
            "df_val": False,
            "df_func": "get_destination",
        },
        "Telheader_TelSeq": {
            "type": "int",
            "length": 6,
            "dp": False,
            "df_val": False,
            "df_func": "get_sequence_number",
        },
        "Telheader_AnlZeit": {
            "type": "datetime",
            "length": 14,
            "dp": False,
            "df_val": False,
            "df_func": "get_current_datetime",
        },
        "Satzart": {
            "type": "str",
            "length": 9,
            "dp": False,
            "df_val": "ARTE00051",
            "df_func": False,
        },
        "Arte_AId_Mand": {
            "type": "str",
            "length": 3,
            "dp": False,
            "dict_key": False,
            "df_val": "000",
            "df_func": False,
        },
        "Arte_AId_ArtNr": {
            "type": "str",
            "length": 20,
            "dp": False,
            "dict_key": "product",
            "df_val": False,
            "df_func": False,
        },
        "Arte_AId_Var": {
            "type": "str",
            "length": 5,
            "dp": False,
            "dict_key": False,
            "df_val": "00000",
            "df_func": False,
        },
        "Arte_Laenge": {
            "type": "int",
            "length": 6,
            "dp": False,
            "dict_key": "length",
            "df_val": False,
            "df_func": False,
        },
        "Arte_Breite": {
            "type": "int",
            "length": 6,
            "dp": False,
            "dict_key": "width",
            "df_val": False,
            "df_func": False,
        },
        "Arte_Hoehe": {
            "type": "int",
            "length": 6,
            "dp": False,
            "dict_key": "height",
            "df_val": False,
            "df_func": False,
        },
        "Arte_Einheit": {
            "type": "str",
            "length": 5,
            "dp": False,
            "dict_key": "package_type",
            "df_val": False,
            "df_func": False,
        },
        "Arte_Zaehler": {
            "type": "int",
            "length": 6,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_Nenner": {
            "type": "int",
            "length": 6,
            "dp": False,
            "dict_key": False,
            "df_val": "000001",
            "df_func": False,
        },
        "Arte_GefGutPunkte": {
            "type": "int",
            "length": 6,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_GEWKS_GewKlasse": {
            "type": "str",
            "length": 6,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_HANDKS_HandKlasse": {
            "type": "str",
            "length": 6,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_Info": {
            "type": "str",
            "length": 5,
            "dp": False,
            "dict_key": "package_type",
            "df_val": False,
            "df_func": False,
        },
        "Arte_InvMngKom": {
            "type": "float",
            "length": 12,
            "dp": 3,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_InvMngTpa": {
            "type": "float",
            "length": 12,
            "dp": 3,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_Lg_AId_Mand": {
            "type": "str",
            "length": 3,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_Lg_AId_ArtNr": {
            "type": "str",
            "length": 20,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_Lg_AId_Var": {
            "type": "str",
            "length": 5,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_NachMng": {
            "type": "float",
            "length": 12,
            "dp": 3,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_TeilNachMng": {
            "type": "float",
            "length": 12,
            "dp": 3,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_OrigTeKz": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_StapelFakt": {
            "type": "float",
            "length": 4,
            "dp": 1,
            "dict_key": False,
            "df_val": "100.0",
            "df_func": False,
        },
        "Arte_TaraGew": {
            "type": "float",
            "length": 12,
            "dp": 3,
            "dict_key": "weight",
            "df_val": False,
            "df_func": False,
        },
        "Arte_WeTeKz": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Arte_SatzKz": {
            "type": "str",
            "length": 1,
            "dp": False,
            "dict_key": "game_identifier",
            "df_val": False,
            "df_func": False,
        },
        "Arte_PrintArtLabWe": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
    }
)
