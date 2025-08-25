import os
import time
import datetime
from scheduler.job_scheduler import JobScheduler, Job
from webbot.test_webbot_html_mapping import readWebPage
from license_llm.pageread_llm import map_json_to_html_fields
from license_llm.license_llm_extractor import extract_vehicle_info_from_image
from backend.logging_utils import log_backend
from backend.memory_store import memory


def run_ts1_extract():
    """
    TS1: JPEG → LLM → JSON
    - Sadece jpg2json çıktısını üretir ve belleği günceller.
    - json2mapping dosyası OLUŞTURMAZ.
    """
    try:
        import json
        memory['state'] = 'başladı'
        log_backend('[INFO] TS1 başlatıldı (run_ts1_extract).', memory, code='BE-4050')
        jpg_download_dir = os.path.join('memory', 'TmpData', 'jpgDownload')
        jpg_files = [f for f in os.listdir(jpg_download_dir) if f.lower().endswith('.jpg')]
        if not jpg_files:
            raise Exception('jpgDownload klasöründe JPEG bulunamadı!')
        latest_jpg = max(jpg_files, key=lambda f: os.path.getmtime(os.path.join(jpg_download_dir, f)))
        latest_path = os.path.join(jpg_download_dir, latest_jpg)
        memory['latest_base'] = os.path.splitext(latest_jpg)[0]
        log_backend(f'[INFO] TS1: Son JPEG: {latest_path}', memory, code='BE-4051', extra={'path': latest_path})

        # LLM çıkarımı
        ruhsat_json = extract_vehicle_info_from_image(latest_path)
        memory['ruhsat_json'] = ruhsat_json
        memory['state'] = 'llm_extracted'
        memory.setdefault('steps', []).append({
            'timestamp': datetime.datetime.now().isoformat(),
            'step': 'llm_extract',
            'ruhsat_json': ruhsat_json,
            'file': latest_path
        })

        # jpg2json'a kaydet
        json_dir = os.path.join('memory', 'TmpData', 'jpg2json')
        os.makedirs(json_dir, exist_ok=True)
        json_filename = os.path.splitext(latest_jpg)[0] + '.json'
        json_path = os.path.join(json_dir, json_filename)
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ruhsat_json, f, ensure_ascii=False, indent=2)
            log_backend(f'[INFO] TS1: JSON dosyası kaydedildi: {json_path}', memory, code='BE-4052', extra={'path': json_path})
        except Exception as file_err:
            # Kaydedilemezse raw metin olarak bırak
            raw_path = os.path.join(json_dir, os.path.splitext(latest_jpg)[0] + '_raw.txt')
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(str(ruhsat_json))
            log_backend(f'[ERROR] TS1: JSON dosyası kaydedilemedi, raw txt: {raw_path} | Hata: {file_err}', memory, code='BE-9101', extra={'path': raw_path})

        log_backend('[INFO] TS1 tamamlandı (mapping YOK).', memory, code='BE-4053')
    except Exception as e:
        memory['state'] = 'hata'
        log_backend(f'[ERROR] TS1 (run_ts1_extract) hata: {e}', memory, code='BE-9102')
        import traceback
        log_backend(traceback.format_exc(), memory, code='BE-9105')
    return 'llm_extracted'

def stateflow_agent():
    try:
        memory['state'] = 'başladı'
        log_backend('[DEBUG] stateflow_agent thread started.', memory, code='BE-4001')
        scheduler = JobScheduler()

        def llm_extract_job():
            import json
            memory['state'] = 'devam ediyor'
            log_backend('[INFO] LLM extract job: Son JPEG dosyası aranıyor...', memory, code='BE-4101')
            jpg_download_dir = os.path.join('memory', 'TmpData', 'jpgDownload')
            jpg_files = [f for f in os.listdir(jpg_download_dir) if f.lower().endswith('.jpg')]
            if not jpg_files:
                raise Exception('jpgDownload klasöründe JPEG bulunamadı!')
            jpg_files.sort(reverse=True)
            latest_jpg = max(jpg_files, key=lambda f: os.path.getmtime(os.path.join(jpg_download_dir, f)))
            latest_path = os.path.join(jpg_download_dir, latest_jpg)
            log_backend(f'[INFO] LLM extract job: Son JPEG: {latest_path}', memory, code='BE-4102', extra={'path': latest_path})
            # Paylaşmak için temel isim sakla
            memory['latest_base'] = os.path.splitext(latest_jpg)[0]
            ruhsat_json = None
            try:
                log_backend(f'[DEBUG] Calling extract_vehicle_info_from_image with: {latest_path}', memory, code='BE-4103')
                ruhsat_json = extract_vehicle_info_from_image(latest_path)
                log_backend(f'[DEBUG] LLM response received', memory, code='BE-4104')
                log_backend(f'[INFO] LLM extract job: JSON çıktı alındı', memory, code='BE-4105')
                memory['ruhsat_json'] = ruhsat_json
                memory['state'] = 'llm_extracted'
                memory['steps'].append({
                    'timestamp': datetime.datetime.now().isoformat(),
                    'step': 'llm_extract',
                    'ruhsat_json': ruhsat_json,
                    'file': latest_path
                })
                # Save JSON to file with same name as JPEG but .json extension in jpg2json folder
                json_dir = os.path.join('memory', 'TmpData', 'jpg2json')
                os.makedirs(json_dir, exist_ok=True)
                json_filename = os.path.splitext(latest_jpg)[0] + '.json'
                json_path = os.path.join(json_dir, json_filename)
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(ruhsat_json, f, ensure_ascii=False, indent=2)
                    log_backend(f'[INFO] LLM extract job: JSON dosyası kaydedildi: {json_path}', memory, code='BE-4106', extra={'path': json_path})
                except Exception as file_err:
                    # If JSON dump fails, save raw response to .txt
                    raw_path = os.path.join(json_dir, os.path.splitext(latest_jpg)[0] + '_raw.txt')
                    with open(raw_path, 'w', encoding='utf-8') as f:
                        f.write(str(ruhsat_json))
                    log_backend(f'[ERROR] JSON dosyası kaydedilemedi, raw response txt olarak kaydedildi: {raw_path} | Hata: {file_err}', memory, code='BE-9101', extra={'path': raw_path})
            except Exception as e:
                log_backend(f'[ERROR] LLM extraction veya dosya kaydı sırasında hata: {e}', memory, code='BE-9102')
            return 'llm_extracted'

        def wait_for_file():
            while memory.get('ruhsat_json') is None:
                time.sleep(0.2)
            return 'file_ready'

        def webbot_job():
            memory['state'] = 'devam ediyor'
            html = readWebPage()
            memory['html'] = html
            memory['steps'].append({
                'timestamp': datetime.datetime.now().isoformat(),
                'step': 'webbot',
                'html_length': len(html)
            })
            log_backend('[INFO] Webbot job: HTML içerik alındı', memory, code='BE-4201', extra={'html_length': len(html)})
            return 'html_ready'

        def memory_job():
            if memory['html']:
                memory['state'] = 'devam ediyor'
                memory['state'] = 'memory_ready'
                return 'memory_ready'
            raise Exception('HTML not in memory')

        def llm_job():
            memory['state'] = 'devam ediyor'
            mapping = map_json_to_html_fields(memory['html'], memory['ruhsat_json'])
            memory['mapping'] = mapping
            memory['steps'].append({
                'timestamp': datetime.datetime.now().isoformat(),
                'step': 'llm_mapping',
                'mapping': mapping
            })
            # mapping'i diske kaydet (json2mapping klasörü)
            try:
                import json
                json2mapping_dir = os.path.join('memory', 'TmpData', 'json2mapping')
                os.makedirs(json2mapping_dir, exist_ok=True)
                base = memory.get('latest_base') or f'mapping_{int(time.time())}'
                mapping_path = os.path.join(json2mapping_dir, f'{base}_mapping.json')
                with open(mapping_path, 'w', encoding='utf-8') as f:
                    json.dump(mapping, f, ensure_ascii=False, indent=2)
                log_backend(f'[INFO] Mapping JSON kaydedildi: {mapping_path}', memory, code='BE-4301', extra={'path': mapping_path})
            except Exception as map_save_err:
                log_backend(f'[ERROR] Mapping JSON kaydedilemedi: {map_save_err}', memory, code='BE-9103')
            memory['state'] = 'tamamlandı'
            return 'llm_done'

        memory['state'] = 'devam ediyor'
        log_backend('[DEBUG] Adding jobs to scheduler.', memory, code='BE-4002')
        scheduler.add_job(Job('llm_extract', llm_extract_job))
        scheduler.add_job(Job('wait_for_file', wait_for_file))
        scheduler.add_job(Job('webbot', webbot_job))
        scheduler.add_job(Job('memory', memory_job))
        scheduler.add_job(Job('llm', llm_job))
        log_backend('[DEBUG] Running all jobs in scheduler.', memory, code='BE-4003')
        scheduler.run_all()
        log_backend('[DEBUG] stateflow_agent finished all jobs.', memory, code='BE-4004')
        return scheduler.get_states()
    except Exception as e:
        memory['state'] = 'hata'
        log_backend(f'[ERROR] stateflow_agent thread crashed: {e}', memory, code='BE-9104')
        import traceback
        log_backend(traceback.format_exc(), memory, code='BE-9105')
