import sys
sys.path.append('backend')
from backend.Features.fillFormsUserTaskPageStatic import plan_analyze_page_static_fill_forms
import json

result = plan_analyze_page_static_fill_forms(
    filtered_html='<button data-lov-id="src/pages/TrafficInsurance.tsx:191:10">Action 1</button>',
    url='https://preview--screen-to-data.lovable.app/traffic-insurance',
    task='Yeni Trafik'
)

print('Analyzer result:')
print(json.dumps(result, indent=2, ensure_ascii=False))