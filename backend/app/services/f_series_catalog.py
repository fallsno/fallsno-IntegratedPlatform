def coerce_float(value):
    if value is None:
        return None
    text = str(value).strip().replace('*', '')
    if not text:
        return None
    return float(text)


def merge_f_series_rows(rows):
    merged = []
    for row in rows:
        ratio = coerce_float(row.get('ratio'))
        radial_load = coerce_float(row.get('radial_load_n'))
        service_factor = coerce_float(row.get('service_factor'))
        power = coerce_float(row.get('power_kw'))
        speed = int(coerce_float(row.get('speed_rpm')))
        torque = int(coerce_float(row.get('torque_nm')))
        gearbox = str(row.get('gearbox') or '').strip()
        motor = str(row.get('motor') or '').strip()

        ratio_text = format(ratio, 'g') if ratio is not None else ''
        merged.append({
            'series': 'F',
            'model': f'{gearbox} {motor}-{ratio_text}',
            'power_kw': power,
            'speed_rpm': speed,
            'torque_nm': torque,
            'ratio': ratio,
            'radial_load_n': int(radial_load) if radial_load is not None else None,
            'service_factor': service_factor,
            'motor': motor,
            'gearbox': gearbox,
        })
    return merged
