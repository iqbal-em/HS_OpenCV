def transform_iklan(values):
    arr = []

    for item in values:
        arr.append(singleTransform_iklan(item))

    return arr


def singleTransform_iklan(values):
    return {
        "id": values.id,
        "name": values.nama,
        "hitung" : values.hitung,
        "url": values.url,
    }

def transform_datacam(values):
    arr = []

    for item in values:
        arr.append(singleTransform_datacam(item))

    return arr


def singleTransform_datacam(values):
    return {
        "id": values.id,
        "id_iklan": values.id_iklan,
        "kode_umur" : values.kode_umur,
        "kode_gender": values.kode_gender, 
        "waktu" : values.waktu,
    }


def transform_peoplecount(values):
    arr = []

    for item in values:
        arr.append(singleTransform_peoplecount(item))

    return arr


def singleTransform_peoplecount(values):
    return {
        "id": values.id,
        "waktu": values.waktu,
        "kode_hs" : values.kode_hs,
    }
