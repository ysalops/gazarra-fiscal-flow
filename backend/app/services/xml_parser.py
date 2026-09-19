from io import BytesIO
import xml.etree.ElementTree as ET
def name(e): return e.tag.split('}')[-1]
def text(parent,key):
    for el in parent.iter():
        if name(el)==key: return (el.text or '').strip()
    return None
def parse_nfe_xml(content:bytes):
    root=ET.parse(BytesIO(content)).getroot(); items=[]; cnpj=None; nf=None
    for el in root.iter():
        if name(el)=='emit' and cnpj is None: cnpj=text(el,'CNPJ')
        if name(el)=='nNF' and nf is None: nf=(el.text or '').strip()
    for det in root.iter():
        if name(det)!='det': continue
        prod=next((c for c in det if name(c)=='prod'),None)
        if prod is None: continue
        items.append({'supplier_code':text(prod,'cProd'),'description':text(prod,'xProd'),'gtin':text(prod,'cEAN'),'ncm':text(prod,'NCM'),'unit':text(prod,'uCom'),'quantity':text(prod,'qCom'),'unit_value':text(prod,'vUnCom')})
    return {'issuer_cnpj':cnpj,'invoice_number':nf,'items':items}
