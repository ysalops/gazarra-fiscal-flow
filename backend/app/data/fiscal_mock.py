FISCAL_MOCK_DATA = {

    # =========================================================
    # CLIENTE 1 - ALPHA
    # =========================================================

    1: {
        "company": {
            "id": 1,
            "name": "Cliente Demonstrativo Alpha",
            "cnpj": "11.111.111/0001-11",
            "tax_regime": "Simples Nacional",
            "city": "São Paulo",
            "state": "SP",
        },

        "competence": "2026-05",

        "revenue": {
            "without_st": 204903.04,
            "with_st": 211324.67,
        },

        "taxes": {
            "das": 20044.13,
            "effective_rate": 9.79,
            "st": 6421.63,
            "difal": 2968.74,
        },

        "simples": {
            "accumulated": 842640.40,
            "limit": 4800000.00,
            "used_percentage": 17.56,
            "remaining_percentage": 82.44,

            "icms_iss_sublimit": 3600000.00,
            "icms_iss_used_percentage": 23.41,
            "icms_iss_remaining_percentage": 76.59,
        },

        "monthly_comparison": [
            {
                "name": "DAS",
                "current_value": 20044.13,
                "previous_value": 16347.02,
                "variation_percentage": 22.62,
            },
            {
                "name": "ST",
                "current_value": 6421.63,
                "previous_value": 8397.64,
                "variation_percentage": -23.53,
            },
            {
                "name": "DIFAL",
                "current_value": 2968.74,
                "previous_value": 3108.97,
                "variation_percentage": -4.51,
            },
        ],

        "yearly_comparison": [
            {
                "name": "DAS",
                "current_value": 20044.13,
                "previous_value": 33949.16,
                "variation_percentage": -40.96,
            },
            {
                "name": "ST",
                "current_value": 6421.63,
                "previous_value": 55355.13,
                "variation_percentage": -88.40,
            },
            {
                "name": "DIFAL",
                "current_value": 2968.74,
                "previous_value": 546.68,
                "variation_percentage": 443.00,
            },
        ],

        "history": [

            # Maio/2025 foi incluído para permitir
            # comparação anual correta com Maio/2026.
            {
                "competence": "2025-05",
                "revenue_without_st": 175000.00,
                "revenue_with_st": 230355.13,
                "das": 33949.16,
                "effective_rate": 14.74,
                "st": 55355.13,
                "difal": 546.68,
            },

            {
                "competence": "2025-06",
                "revenue_without_st": 199291.27,
                "revenue_with_st": 242689.13,
                "das": 33505.65,
                "effective_rate": 13.81,
                "st": 43407.86,
                "difal": 1850.00,
            },

            {
                "competence": "2025-07",
                "revenue_without_st": 111963.81,
                "revenue_with_st": 151104.53,
                "das": 16829.20,
                "effective_rate": 11.14,
                "st": 39140.72,
                "difal": 1420.00,
            },

            {
                "competence": "2025-08",
                "revenue_without_st": 69156.06,
                "revenue_with_st": 93096.88,
                "das": 8505.49,
                "effective_rate": 9.14,
                "st": 23940.82,
                "difal": 1280.00,
            },

            {
                "competence": "2025-09",
                "revenue_without_st": 143850.84,
                "revenue_with_st": 194383.82,
                "das": 17325.49,
                "effective_rate": 8.91,
                "st": 50532.98,
                "difal": 1950.00,
            },

            {
                "competence": "2025-10",
                "revenue_without_st": 77767.16,
                "revenue_with_st": 102670.99,
                "das": 9234.13,
                "effective_rate": 8.99,
                "st": 24903.83,
                "difal": 1740.00,
            },

            {
                "competence": "2025-11",
                "revenue_without_st": 81784.11,
                "revenue_with_st": 109399.96,
                "das": 9479.08,
                "effective_rate": 8.67,
                "st": 27615.85,
                "difal": 1630.00,
            },

            {
                "competence": "2025-12",
                "revenue_without_st": 143851.84,
                "revenue_with_st": 134474.95,
                "das": 11126.99,
                "effective_rate": 7.80,
                "st": 8744.41,
                "difal": 2120.00,
            },

            {
                "competence": "2026-01",
                "revenue_without_st": 171328.35,
                "revenue_with_st": 180072.76,
                "das": 18390.34,
                "effective_rate": 10.73,
                "st": 7876.18,
                "difal": 2450.00,
            },

            {
                "competence": "2026-02",
                "revenue_without_st": 168733.51,
                "revenue_with_st": 176609.69,
                "das": 17381.60,
                "effective_rate": 10.30,
                "st": 7876.18,
                "difal": 2650.00,
            },

            {
                "competence": "2026-03",
                "revenue_without_st": 130683.10,
                "revenue_with_st": 143036.44,
                "das": 13483.80,
                "effective_rate": 10.32,
                "st": 12353.34,
                "difal": 2840.00,
            },

            {
                "competence": "2026-04",
                "revenue_without_st": 166992.40,
                "revenue_with_st": 175390.04,
                "das": 16347.02,
                "effective_rate": 9.79,
                "st": 8397.64,
                "difal": 3108.97,
            },

            {
                "competence": "2026-05",
                "revenue_without_st": 204903.04,
                "revenue_with_st": 211324.67,
                "das": 20044.13,
                "effective_rate": 9.79,
                "st": 6421.63,
                "difal": 2968.74,
            },
        ],

        "st_by_state": [
            {
                "state": "MG",
                "cfop": "5401002",
                "product": "Produto Demonstrativo A",
                "invoice_value": 6077.00,
                "st_value": 1123.08,
            },
            {
                "state": "PA",
                "cfop": "6401002",
                "product": "Produto Demonstrativo B",
                "invoice_value": 4014.92,
                "st_value": 1314.67,
            },
            {
                "state": "ES",
                "cfop": "6401002",
                "product": "Produto Demonstrativo A",
                "invoice_value": 2572.15,
                "st_value": 1374.69,
            },
        ],

        "difal_details": [
            {
                "supplier": "Fornecedor Demonstrativo 01",
                "invoice_number": "8869",
                "document_value": 2143.63,
                "calculation_base": 2100.48,
                "icms_advance": 156.83,
            },
            {
                "supplier": "Fornecedor Demonstrativo 02",
                "invoice_number": "82254",
                "document_value": 18697.15,
                "calculation_base": 21595.10,
                "icms_advance": 2811.91,
            },
        ],

        "certificates": [
            {
                "type": "Federal",
                "status": "Regular",
                "issued_at": "2026-06-15",
                "expires_at": "2026-12-12",
            },
            {
                "type": "Estadual",
                "status": "Regular",
                "issued_at": "2026-06-18",
                "expires_at": "2026-09-16",
            },
            {
                "type": "Municipal",
                "status": "Regular",
                "issued_at": "2026-06-18",
                "expires_at": "2026-07-18",
            },
        ],

        "obligations": [
            {
                "name": "Simples Nacional",
                "competence": "2026-05",
                "delivered_at": "2026-06-02",
                "due_at": "2026-06-20",
                "status": "Entregue",
            },
            {
                "name": "DESTDA",
                "competence": "2026-05",
                "delivered_at": "2026-06-02",
                "due_at": "2026-06-30",
                "status": "Entregue",
            },
        ],
    },


    # =========================================================
    # CLIENTE 2 - BETA
    # =========================================================

    2: {
        "company": {
            "id": 2,
            "name": "Cliente Demonstrativo Beta",
            "cnpj": "22.222.222/0001-22",
            "tax_regime": "Simples Nacional",
            "city": "Campinas",
            "state": "SP",
        },

        "competence": "2026-05",

        "revenue": {
            "without_st": 148750.35,
            "with_st": 158430.20,
        },

        "taxes": {
            "das": 14280.50,
            "effective_rate": 9.60,
            "st": 9679.85,
            "difal": 1850.20,
        },

        "simples": {
            "accumulated": 718550.00,
            "limit": 4800000.00,
            "used_percentage": 14.97,
            "remaining_percentage": 85.03,

            "icms_iss_sublimit": 3600000.00,
            "icms_iss_used_percentage": 19.96,
            "icms_iss_remaining_percentage": 80.04,
        },

        "monthly_comparison": [
            {
                "name": "DAS",
                "current_value": 14280.50,
                "previous_value": 13110.30,
                "variation_percentage": 8.93,
            },
            {
                "name": "ST",
                "current_value": 9679.85,
                "previous_value": 10340.10,
                "variation_percentage": -6.39,
            },
            {
                "name": "DIFAL",
                "current_value": 1850.20,
                "previous_value": 1720.00,
                "variation_percentage": 7.57,
            },
        ],

        "yearly_comparison": [
            {
                "name": "DAS",
                "current_value": 14280.50,
                "previous_value": 12150.00,
                "variation_percentage": 17.53,
            },
            {
                "name": "ST",
                "current_value": 9679.85,
                "previous_value": 11500.00,
                "variation_percentage": -15.83,
            },
            {
                "name": "DIFAL",
                "current_value": 1850.20,
                "previous_value": 1600.00,
                "variation_percentage": 15.64,
            },
        ],

        "history": [

            {
                "competence": "2025-05",
                "revenue_without_st": 98000.00,
                "revenue_with_st": 105500.00,
                "das": 12150.00,
                "effective_rate": 11.52,
                "st": 11500.00,
                "difal": 1600.00,
            },

            {
                "competence": "2025-06",
                "revenue_without_st": 102000.00,
                "revenue_with_st": 108500.00,
                "das": 9950.00,
                "effective_rate": 9.75,
                "st": 6500.00,
                "difal": 1200.00,
            },

            {
                "competence": "2025-07",
                "revenue_without_st": 108000.00,
                "revenue_with_st": 115000.00,
                "das": 10200.00,
                "effective_rate": 9.44,
                "st": 7000.00,
                "difal": 1250.00,
            },

            {
                "competence": "2025-08",
                "revenue_without_st": 112500.00,
                "revenue_with_st": 119900.00,
                "das": 10600.00,
                "effective_rate": 9.42,
                "st": 7400.00,
                "difal": 1300.00,
            },

            {
                "competence": "2025-09",
                "revenue_without_st": 118400.00,
                "revenue_with_st": 126100.00,
                "das": 11100.00,
                "effective_rate": 9.38,
                "st": 7700.00,
                "difal": 1380.00,
            },

            {
                "competence": "2025-10",
                "revenue_without_st": 121500.00,
                "revenue_with_st": 129700.00,
                "das": 11500.00,
                "effective_rate": 9.47,
                "st": 8200.00,
                "difal": 1420.00,
            },

            {
                "competence": "2025-11",
                "revenue_without_st": 126800.00,
                "revenue_with_st": 135400.00,
                "das": 12000.00,
                "effective_rate": 9.46,
                "st": 8600.00,
                "difal": 1480.00,
            },

            {
                "competence": "2025-12",
                "revenue_without_st": 131000.00,
                "revenue_with_st": 140200.00,
                "das": 12400.00,
                "effective_rate": 9.47,
                "st": 9200.00,
                "difal": 1500.00,
            },

            {
                "competence": "2026-01",
                "revenue_without_st": 135000.00,
                "revenue_with_st": 144500.00,
                "das": 12650.00,
                "effective_rate": 9.37,
                "st": 9500.00,
                "difal": 1550.00,
            },

            {
                "competence": "2026-02",
                "revenue_without_st": 138000.00,
                "revenue_with_st": 147500.00,
                "das": 12900.00,
                "effective_rate": 9.35,
                "st": 9500.00,
                "difal": 1600.00,
            },

            {
                "competence": "2026-03",
                "revenue_without_st": 141500.00,
                "revenue_with_st": 151000.00,
                "das": 13050.00,
                "effective_rate": 9.22,
                "st": 9500.00,
                "difal": 1660.00,
            },

            {
                "competence": "2026-04",
                "revenue_without_st": 144300.00,
                "revenue_with_st": 154640.10,
                "das": 13110.30,
                "effective_rate": 9.09,
                "st": 10340.10,
                "difal": 1720.00,
            },

            {
                "competence": "2026-05",
                "revenue_without_st": 148750.35,
                "revenue_with_st": 158430.20,
                "das": 14280.50,
                "effective_rate": 9.60,
                "st": 9679.85,
                "difal": 1850.20,
            },
        ],

        "st_by_state": [
            {
                "state": "SP",
                "cfop": "5405001",
                "product": "Produto Demonstrativo C",
                "invoice_value": 9500.00,
                "st_value": 3200.00,
            },
            {
                "state": "RJ",
                "cfop": "6404001",
                "product": "Produto Demonstrativo D",
                "invoice_value": 11200.00,
                "st_value": 4100.00,
            },
        ],

        "difal_details": [
            {
                "supplier": "Fornecedor Beta 01",
                "invoice_number": "4501",
                "document_value": 11800.00,
                "calculation_base": 12300.00,
                "icms_advance": 1250.20,
            },
            {
                "supplier": "Fornecedor Beta 02",
                "invoice_number": "8890",
                "document_value": 5700.00,
                "calculation_base": 5900.00,
                "icms_advance": 600.00,
            },
        ],

        "certificates": [
            {
                "type": "Federal",
                "status": "Regular",
                "issued_at": "2026-05-20",
                "expires_at": "2026-11-16",
            },
            {
                "type": "Estadual",
                "status": "Regular",
                "issued_at": "2026-06-01",
                "expires_at": "2026-09-30",
            },
            {
                "type": "Municipal",
                "status": "A vencer",
                "issued_at": "2026-06-10",
                "expires_at": "2026-07-10",
            },
        ],

        "obligations": [
            {
                "name": "Simples Nacional",
                "competence": "2026-05",
                "delivered_at": "2026-06-05",
                "due_at": "2026-06-20",
                "status": "Entregue",
            },
            {
                "name": "DESTDA",
                "competence": "2026-05",
                "delivered_at": None,
                "due_at": "2026-06-30",
                "status": "Pendente",
            },
        ],
    },


    # =========================================================
    # CLIENTE 3 - GAMMA
    # =========================================================

    3: {
        "company": {
            "id": 3,
            "name": "Cliente Demonstrativo Gamma",
            "cnpj": "33.333.333/0001-33",
            "tax_regime": "Simples Nacional",
            "city": "Belo Horizonte",
            "state": "MG",
        },

        "competence": "2026-05",

        "revenue": {
            "without_st": 326850.90,
            "with_st": 348790.40,
        },

        "taxes": {
            "das": 34550.75,
            "effective_rate": 10.57,
            "st": 21939.50,
            "difal": 5480.90,
        },

        "simples": {
            "accumulated": 1758000.00,
            "limit": 4800000.00,
            "used_percentage": 36.63,
            "remaining_percentage": 63.37,

            "icms_iss_sublimit": 3600000.00,
            "icms_iss_used_percentage": 48.83,
            "icms_iss_remaining_percentage": 51.17,
        },

        "monthly_comparison": [
            {
                "name": "DAS",
                "current_value": 34550.75,
                "previous_value": 31980.20,
                "variation_percentage": 8.04,
            },
            {
                "name": "ST",
                "current_value": 21939.50,
                "previous_value": 20550.00,
                "variation_percentage": 6.76,
            },
            {
                "name": "DIFAL",
                "current_value": 5480.90,
                "previous_value": 5200.00,
                "variation_percentage": 5.40,
            },
        ],

        "yearly_comparison": [
            {
                "name": "DAS",
                "current_value": 34550.75,
                "previous_value": 28700.00,
                "variation_percentage": 20.39,
            },
            {
                "name": "ST",
                "current_value": 21939.50,
                "previous_value": 18500.00,
                "variation_percentage": 18.59,
            },
            {
                "name": "DIFAL",
                "current_value": 5480.90,
                "previous_value": 4300.00,
                "variation_percentage": 27.46,
            },
        ],

        "history": [

            {
                "competence": "2025-05",
                "revenue_without_st": 205000.00,
                "revenue_with_st": 218500.00,
                "das": 28700.00,
                "effective_rate": 13.14,
                "st": 18500.00,
                "difal": 4300.00,
            },

            {
                "competence": "2025-06",
                "revenue_without_st": 212000.00,
                "revenue_with_st": 225000.00,
                "das": 22100.00,
                "effective_rate": 10.42,
                "st": 13000.00,
                "difal": 3500.00,
            },

            {
                "competence": "2025-07",
                "revenue_without_st": 220000.00,
                "revenue_with_st": 234000.00,
                "das": 22900.00,
                "effective_rate": 10.41,
                "st": 14000.00,
                "difal": 3650.00,
            },

            {
                "competence": "2025-08",
                "revenue_without_st": 231000.00,
                "revenue_with_st": 246500.00,
                "das": 24100.00,
                "effective_rate": 10.43,
                "st": 15500.00,
                "difal": 3800.00,
            },

            {
                "competence": "2025-09",
                "revenue_without_st": 240500.00,
                "revenue_with_st": 257000.00,
                "das": 25100.00,
                "effective_rate": 10.44,
                "st": 16500.00,
                "difal": 4000.00,
            },

            {
                "competence": "2025-10",
                "revenue_without_st": 251000.00,
                "revenue_with_st": 268500.00,
                "das": 26300.00,
                "effective_rate": 10.48,
                "st": 17500.00,
                "difal": 4200.00,
            },

            {
                "competence": "2025-11",
                "revenue_without_st": 264000.00,
                "revenue_with_st": 282500.00,
                "das": 27800.00,
                "effective_rate": 10.53,
                "st": 18500.00,
                "difal": 4400.00,
            },

            {
                "competence": "2025-12",
                "revenue_without_st": 278500.00,
                "revenue_with_st": 297500.00,
                "das": 29300.00,
                "effective_rate": 10.52,
                "st": 19000.00,
                "difal": 4600.00,
            },

            {
                "competence": "2026-01",
                "revenue_without_st": 287000.00,
                "revenue_with_st": 306500.00,
                "das": 30200.00,
                "effective_rate": 10.52,
                "st": 19500.00,
                "difal": 4750.00,
            },

            {
                "competence": "2026-02",
                "revenue_without_st": 296500.00,
                "revenue_with_st": 316500.00,
                "das": 31200.00,
                "effective_rate": 10.52,
                "st": 20000.00,
                "difal": 4900.00,
            },

            {
                "competence": "2026-03",
                "revenue_without_st": 307000.00,
                "revenue_with_st": 327000.00,
                "das": 32200.00,
                "effective_rate": 10.49,
                "st": 20000.00,
                "difal": 5050.00,
            },

            {
                "competence": "2026-04",
                "revenue_without_st": 315500.00,
                "revenue_with_st": 336050.00,
                "das": 31980.20,
                "effective_rate": 10.14,
                "st": 20550.00,
                "difal": 5200.00,
            },

            {
                "competence": "2026-05",
                "revenue_without_st": 326850.90,
                "revenue_with_st": 348790.40,
                "das": 34550.75,
                "effective_rate": 10.57,
                "st": 21939.50,
                "difal": 5480.90,
            },
        ],

        "st_by_state": [
            {
                "state": "MG",
                "cfop": "5405001",
                "product": "Produto Demonstrativo E",
                "invoice_value": 28500.00,
                "st_value": 8750.00,
            },
            {
                "state": "GO",
                "cfop": "6404001",
                "product": "Produto Demonstrativo F",
                "invoice_value": 22300.00,
                "st_value": 7340.00,
            },
            {
                "state": "BA",
                "cfop": "6404001",
                "product": "Produto Demonstrativo G",
                "invoice_value": 19100.00,
                "st_value": 5849.50,
            },
        ],

        "difal_details": [
            {
                "supplier": "Fornecedor Gamma 01",
                "invoice_number": "12001",
                "document_value": 25000.00,
                "calculation_base": 26800.00,
                "icms_advance": 3100.90,
            },
            {
                "supplier": "Fornecedor Gamma 02",
                "invoice_number": "14409",
                "document_value": 17800.00,
                "calculation_base": 18500.00,
                "icms_advance": 2380.00,
            },
        ],

        "certificates": [
            {
                "type": "Federal",
                "status": "Regular",
                "issued_at": "2026-06-03",
                "expires_at": "2026-11-30",
            },
            {
                "type": "Estadual",
                "status": "Regular",
                "issued_at": "2026-06-15",
                "expires_at": "2026-10-15",
            },
            {
                "type": "Municipal",
                "status": "Regular",
                "issued_at": "2026-06-11",
                "expires_at": "2026-09-11",
            },
        ],

        "obligations": [
            {
                "name": "Simples Nacional",
                "competence": "2026-05",
                "delivered_at": "2026-06-03",
                "due_at": "2026-06-20",
                "status": "Entregue",
            },
            {
                "name": "DESTDA",
                "competence": "2026-05",
                "delivered_at": "2026-06-10",
                "due_at": "2026-06-30",
                "status": "Entregue",
            },
        ],
    },
}