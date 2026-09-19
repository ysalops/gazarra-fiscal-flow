from app.services.product_matcher import suggest
def test_match():
    s={'description':'Açúcar cristal 5kg','gtin':'7890000000011','ncm':'17019900','unit':'UN'}
    c=[{'internal_code':'PRD-001','description':'Açúcar Cristal 5 KG','gtin':'7890000000011','ncm':'17019900','unit':'UN'}]
    r=suggest(s,c)
    assert r['internal_code']=='PRD-001'
    assert r['confidence']>=.90
