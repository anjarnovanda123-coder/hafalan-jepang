import streamlit as st
import json
import random
import os

# =========================================================
#  KONFIGURASI HALAMAN
# =========================================================
st.set_page_config(
    page_title="Hafalan Bahasa Jepang - Indonesia",
    page_icon="🎌",
    layout="wide"
)

# =========================================================
#  KONFIGURASI FILE
# =========================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER_DATA = os.path.join(SCRIPT_DIR, "kosakata_data")

try:
    if not os.path.exists(FOLDER_DATA):
        os.makedirs(FOLDER_DATA, exist_ok=True)
except (FileExistsError, PermissionError, OSError):
    pass

if not os.path.isdir(FOLDER_DATA):
    FOLDER_DATA = "/tmp/kosakata_data"
    try:
        os.makedirs(FOLDER_DATA, exist_ok=True)
    except Exception:
        pass


# =========================================================
#  FUNGSI BANTU
# =========================================================
def daftar_file_tersimpan():
    try:
        if not os.path.isdir(FOLDER_DATA):
            return []
        files = [f for f in os.listdir(FOLDER_DATA)
                 if f.endswith(".json") and f != "_aktif.json"]
        return sorted(files)
    except Exception:
        return []


def path_file(nama):
    return os.path.join(FOLDER_DATA, nama)


def muat_data(nama_file):
    path = path_file(nama_file)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        data_bersih = []
        for item in data:
            if isinstance(item, dict) and "indo" in item and "jepang" in item:
                data_bersih.append({
                    "indo": str(item["indo"]),
                    "jepang": str(item["jepang"]),
                    "huruf": str(item.get("huruf", ""))
                })
        return data_bersih
    except Exception:
        return []


def simpan_data(nama_file, data):
    path = path_file(nama_file)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def kunci_unik(kata):
    return (kata["indo"].lower().strip(),
            kata["jepang"].lower().strip())


# =========================================================
#  SESSION STATE
# =========================================================
def init_session_state():
    defaults = {
        "halaman": "menu",
        "file_aktif": None,
        "data_kosakata": [],
        "mode_kuis": "jepang_ke_indo",
        "target_benar": 2,
        "sesi_aktif": False,
        "sesi_kata_unik": [],
        "sesi_progress": {},
        "sesi_total_salah": 0,
        "sesi_total_percobaan": 0,
        "sesi_total_benar_mentah": 0,
        "antrian_soal": [],
        "soal_sekarang": None,
        "sudah_dijawab": False,
        "pesan_feedback": None,
        "tipe_feedback": None,
        "range_mulai": 1,
        "range_selesai": 10,
        "data_pemahaman": [],
        "pilihan_jawaban": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# =========================================================
#  SIDEBAR
# =========================================================
def render_sidebar():
    with st.sidebar:
        st.header("📁 Manajemen File")

        files = daftar_file_tersimpan()

        if not files:
            try:
                simpan_data("default.json", [])
                files = ["default.json"]
            except Exception:
                st.warning("Tidak bisa membuat file data.")
                return

        if st.session_state.file_aktif not in files:
            st.session_state.file_aktif = files[0]
            st.session_state.data_kosakata = muat_data(files[0])

        idx_aktif = files.index(st.session_state.file_aktif) \
            if st.session_state.file_aktif in files else 0

        pilihan = st.selectbox("Pilih file aktif:", files, index=idx_aktif)

        if pilihan != st.session_state.file_aktif:
            st.session_state.file_aktif = pilihan
            st.session_state.data_kosakata = muat_data(pilihan)
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            nama_baru = st.text_input("File baru:", value="", key="file_baru_input")
            if st.button("➕ Buat", use_container_width=True):
                if nama_baru.strip():
                    nama = nama_baru.strip().replace(" ", "_")
                    if not nama.lower().endswith(".json"):
                        nama += ".json"
                    if os.path.exists(path_file(nama)):
                        st.error("File sudah ada!")
                    else:
                        simpan_data(nama, [])
                        st.session_state.file_aktif = nama
                        st.session_state.data_kosakata = []
                        st.rerun()

        with col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Hapus File", use_container_width=True):
                if len(files) <= 1:
                    st.error("Harus ada minimal 1 file!")
                else:
                    try:
                        os.remove(path_file(st.session_state.file_aktif))
                        sisa = [f for f in files
                                if f != st.session_state.file_aktif]
                        st.session_state.file_aktif = sisa[0]
                        st.session_state.data_kosakata = muat_data(sisa[0])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal hapus: {e}")

        st.divider()
        st.header("➕ Tambah Kosakata")

        with st.form("form_tambah", clear_on_submit=True):
            indo = st.text_input("🇮🇩 Bahasa Indonesia:")
            jepang = st.text_input("🔤 Romaji:")
            huruf = st.text_input("🇯🇵 Huruf Jepang (opsional):")
            submit = st.form_submit_button("Tambah", use_container_width=True)

            if submit:
                if not indo or not jepang:
                    st.error("Indonesia dan Romaji wajib diisi!")
                else:
                    data = st.session_state.data_kosakata
                    baru = {
                        "indo": indo.strip(),
                        "jepang": jepang.strip(),
                        "huruf": huruf.strip()
                    }
                    duplikat = any(
                        kunci_unik(d) == kunci_unik(baru) for d in data
                    )
                    if duplikat:
                        st.warning("Kosakata ini sudah ada!")
                    else:
                        data.append(baru)
                        simpan_data(st.session_state.file_aktif, data)
                        st.success("Ditambahkan!")
                        st.rerun()

        st.divider()
        st.caption(f"📄 File aktif: **{st.session_state.file_aktif}**")
        st.caption(f"📚 Total: **{len(st.session_state.data_kosakata)}** kata")


# =========================================================
#  HALAMAN MENU
# =========================================================
def render_menu():
    st.title("🎌 Hafalan Bahasa Jepang - Bahasa Indonesia 🎌")
    st.caption(f"📁 Folder data: `{FOLDER_DATA}`")

    data = st.session_state.data_kosakata

    if not data:
        st.info("📭 Belum ada kosakata di file ini. Tambahkan kata dulu di sidebar.")
        return

    st.subheader(f"📋 Kosakata di File Aktif ({len(data)} kata)")

    tabel_data = []
    for i, kos in enumerate(data, 1):
        tabel_data.append({
            "No": i,
            "🇮🇩 Indonesia": kos["indo"],
            "🔤 Romaji": kos["jepang"],
            "🇯🇵 Huruf Jepang": kos.get("huruf", "")
        })
    st.dataframe(tabel_data, use_container_width=True, height=300)

    if st.button("🧹 Hapus Semua Kosakata"):
        st.session_state.data_kosakata = []
        simpan_data(st.session_state.file_aktif, [])
        st.rerun()

    st.divider()
    st.subheader("🎯 Mulai Kuis / Pemahaman")

    col1, col2 = st.columns(2)
    with col1:
        mulai = st.number_input("Dari nomor:", min_value=1,
                                max_value=len(data), value=1)
    with col2:
        selesai = st.number_input("Sampai nomor:", min_value=1,
                                  max_value=len(data),
                                  value=min(10, len(data)))

    if mulai > selesai:
        st.error("Nomor awal tidak boleh lebih besar dari nomor akhir!")
        return

    st.caption(
        f"🎯 Target sesi: setiap kata harus benar "
        f"**{st.session_state.target_benar}x**. Salah = reset ke 0."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮 MULAI KUIS", use_container_width=True, type="primary"):
            mulai_kuis(mulai, selesai)
    with col2:
        if st.button("📖 MODE PEMAHAMAN", use_container_width=True):
            mulai_pemahaman(mulai, selesai)


# =========================================================
#  LOGIKA MULAI
# =========================================================
def mulai_kuis(mulai, selesai):
    data = st.session_state.data_kosakata
    kata_range = data[mulai - 1:selesai]

    if not kata_range:
        st.error("Tidak ada kata dalam range tersebut!")
        return

    unik = []
    sudah_ada = set()
    for k in kata_range:
        kunci = kunci_unik(k)
        if kunci not in sudah_ada:
            sudah_ada.add(kunci)
            unik.append(k)

    st.session_state.sesi_aktif = True
    st.session_state.sesi_kata_unik = list(unik)
    st.session_state.sesi_progress = {kunci_unik(k): 0 for k in unik}
    st.session_state.sesi_total_salah = 0
    st.session_state.sesi_total_percobaan = 0
    st.session_state.sesi_total_benar_mentah = 0
    st.session_state.antrian_soal = list(unik)
    random.shuffle(st.session_state.antrian_soal)
    st.session_state.range_mulai = mulai
    st.session_state.range_selesai = selesai
    st.session_state.halaman = "kuis"
    st.session_state.soal_sekarang = None
    st.session_state.sudah_dijawab = False
    st.session_state.pesan_feedback = None
    st.session_state.pilihan_jawaban = []
    st.rerun()


def mulai_pemahaman(mulai, selesai):
    data = st.session_state.data_kosakata
    kata_range = data[mulai - 1:selesai]

    if not kata_range:
        st.error("Tidak ada kata dalam range tersebut!")
        return

    st.session_state.range_mulai = mulai
    st.session_state.range_selesai = selesai
    st.session_state.halaman = "pemahaman"
    st.session_state.data_pemahaman = list(kata_range)
    st.rerun()


# =========================================================
#  HALAMAN KUIS
# =========================================================
def render_kuis():
    if st.session_state.sesi_aktif:
        total_tuntas = sum(
            1 for v in st.session_state.sesi_progress.values()
            if v >= st.session_state.target_benar
        )
        if total_tuntas >= len(st.session_state.sesi_kata_unik):
            selesaikan_sesi()
            return

    st.title("🎮 MODE KUIS 🎮")
    st.caption(
        f"📚 Nomor {st.session_state.range_mulai}-{st.session_state.range_selesai} "
        f"({len(st.session_state.sesi_kata_unik)} kata unik, target "
        f"{st.session_state.target_benar}x) • "
        f"📄 {st.session_state.file_aktif}"
    )

    total_benar = sum(st.session_state.sesi_progress.values())
    target = len(st.session_state.sesi_kata_unik) * st.session_state.target_benar
    persen = min(total_benar / target, 1.0) if target > 0 else 0

    st.progress(persen)
    st.caption(
        f"📝 Benar: {total_benar}/{target} jawaban | "
        f"❌ Salah: {st.session_state.sesi_total_salah} | "
        f"🔁 Percobaan: {st.session_state.sesi_total_percobaan} | "
        f"✅ Tuntas: "
        f"{sum(1 for v in st.session_state.sesi_progress.values() if v >= st.session_state.target_benar)}"
        f"/{len(st.session_state.sesi_kata_unik)} kata"
    )

    mode = st.radio(
        "Mode:",
        ["jepang_ke_indo", "indo_ke_jepang"],
        format_func=lambda x: "🇯🇵 Jepang → Indonesia"
        if x == "jepang_ke_indo" else "🇮🇩 Indonesia → Jepang",
        horizontal=True,
        key="mode_kuis_radio"
    )

    if mode != st.session_state.mode_kuis:
        st.session_state.mode_kuis = mode
        st.session_state.soal_sekarang = None
        st.session_state.sudah_dijawab = False
        st.session_state.pesan_feedback = None
        st.session_state.pilihan_jawaban = []

    st.divider()

    if st.session_state.soal_sekarang is None:
        if not st.session_state.antrian_soal:
            st.session_state.antrian_soal = list(st.session_state.sesi_kata_unik)
            random.shuffle(st.session_state.antrian_soal)
        st.session_state.soal_sekarang = st.session_state.antrian_soal.pop(0)
        st.session_state.sudah_dijawab = False
        st.session_state.pilihan_jawaban = []
        st.session_state.pesan_feedback = None

    soal = st.session_state.soal_sekarang
    huruf = soal.get("huruf", "")

    if st.session_state.mode_kuis == "jepang_ke_indo":
        st.markdown(f"### 🇯🇵 {soal['jepang']}")
        if huruf:
            st.markdown(f"## {huruf}")
        st.caption("Apa bahasa Indonesianya?")
    else:
        st.markdown(f"### 🇮🇩 {soal['indo']}")
        st.caption("Apa bahasa Jepangnya? (romaji)")

    if st.session_state.pesan_feedback:
        if st.session_state.tipe_feedback == "benar":
            st.success(st.session_state.pesan_feedback)
        elif st.session_state.tipe_feedback == "salah":
            st.error(st.session_state.pesan_feedback)
        else:
            st.info(st.session_state.pesan_feedback)

    if not st.session_state.sudah_dijawab:
        buat_tombol_jawaban(soal)
    else:
        if st.button("➡️ Lanjut ke Soal Berikutnya",
                     type="primary", use_container_width=True):
            st.session_state.soal_sekarang = None
            st.session_state.sudah_dijawab = False
            st.session_state.pesan_feedback = None
            st.session_state.pilihan_jawaban = []
            st.rerun()

    st.divider()
    if st.button("🚪 Keluar ke Menu Utama", use_container_width=True):
        reset_sesi()
        st.session_state.halaman = "menu"
        st.rerun()


def buat_tombol_jawaban(soal):
    mode = st.session_state.mode_kuis
    semua_kata = st.session_state.sesi_kata_unik

    if mode == "jepang_ke_indo":
        kunci_benar = soal["indo"]
    else:
        kunci_benar = soal["jepang"]

    # Kalau pilihan sudah dibuat, pakai yang lama
    if not st.session_state.pilihan_jawaban:
        item_benar = None
        pengecoh = []
        for item in semua_kata:
            nilai = item["indo"] if mode == "jepang_ke_indo" else item["jepang"]
            if nilai == kunci_benar and item_benar is None:
                item_benar = item
            else:
                pengecoh.append(item)

        if item_benar is None:
            item_benar = soal

        random.shuffle(pengecoh)

        teks_sudah_ada = set()
        teks_sudah_ada.add(" ".join(kunci_benar.lower().split()))

        pengecoh_unik = []
        for item in pengecoh:
            nilai = item["indo"] if mode == "jepang_ke_indo" else item["jepang"]
            kunci_teks = " ".join(nilai.lower().split())
            if kunci_teks not in teks_sudah_ada:
                teks_sudah_ada.add(kunci_teks)
                pengecoh_unik.append(item)

        maks_pilihan = 15
        jumlah_pengecoh = max(maks_pilihan - 1, 1)
        pilihan_final = [item_benar] + pengecoh_unik[:jumlah_pengecoh]
        random.shuffle(pilihan_final)
        st.session_state.pilihan_jawaban = pilihan_final

    pilihan_final = st.session_state.pilihan_jawaban

    st.write("**🎮 Pilih Jawaban:**")

    # Buat tombol grid 3 kolom
    n_cols = 3
    rows = [pilihan_final[i:i + n_cols]
            for i in range(0, len(pilihan_final), n_cols)]

    for row_idx, row in enumerate(rows):
        kolom = st.columns(len(row))
        for col_idx in range(len(row)):
            item = row[col_idx]

            if mode == "jepang_ke_indo":
                label = item["indo"]
            else:
                label = item["jepang"]
                if item.get("huruf"):
                    label += f" ({item['huruf']})"

            unique_key = f"jwb_{row_idx}_{col_idx}"

            with kolom[col_idx]:
                if st.button(label, use_container_width=True, key=unique_key):
                    proses_jawaban(label, kunci_benar)


def proses_jawaban(jawaban_dipilih, kunci_benar):
    soal = st.session_state.soal_sekarang
    norm = lambda s: " ".join(str(s).lower().split())
    benar = norm(jawaban_dipilih) == norm(kunci_benar)

    kunci_kata = kunci_unik(soal)
    st.session_state.sesi_total_percobaan += 1

    if benar:
        st.session_state.sesi_total_benar_mentah += 1
        progress_lama = st.session_state.sesi_progress.get(kunci_kata, 0)
        if progress_lama < st.session_state.target_benar:
            st.session_state.sesi_progress[kunci_kata] = progress_lama + 1
    else:
        st.session_state.sesi_progress[kunci_kata] = 0
        st.session_state.sesi_total_salah += 1

    st.session_state.antrian_soal.append(soal)
    st.session_state.sudah_dijawab = True

    huruf = soal.get("huruf", "")
    pesan_benar = f"{soal['jepang']}"
    if huruf:
        pesan_benar += f" ({huruf})"
    pesan_benar += f" = {kunci_benar}"

    if benar:
        st.session_state.pesan_feedback = f"✅ Jawaban Benar!\n\n{pesan_benar}"
        st.session_state.tipe_feedback = "benar"
    else:
        st.session_state.pesan_feedback = (
            f"❌ Jawaban Salah\n\n"
            f"Jawaban kamu: {jawaban_dipilih}\n\n"
            f"Jawaban benar: **{kunci_benar}**\n\n"
            f"{pesan_benar}"
        )
        st.session_state.tipe_feedback = "salah"

    st.rerun()


def selesaikan_sesi():
    st.session_state.sesi_aktif = False

    total_unik = len(st.session_state.sesi_kata_unik)
    total_benar = sum(st.session_state.sesi_progress.values())
    target = total_unik * st.session_state.target_benar
    tuntas = sum(1 for v in st.session_state.sesi_progress.values()
                 if v >= st.session_state.target_benar)
    percobaan = st.session_state.sesi_total_percobaan
    salah = st.session_state.sesi_total_salah

    skor = int((total_benar / target) * 100) if target > 0 else 0
    skor = min(skor, 100)

    kualitas = int(
        (st.session_state.sesi_total_benar_mentah / percobaan) * 100
    ) if percobaan > 0 else 0

    if skor >= 100:
        status = "MAHIR! 🏆"
    elif skor >= 80:
        status = "Bagus 👍"
    elif skor >= 60:
        status = "Cukup 🙂"
    elif skor >= 40:
        status = "Perlu Latihan ⚠️"
    else:
        status = "Belum Mahir ❌"

    st.balloons()
    st.title("🎉 Sesi Kuis Selesai!")
    st.markdown(f"## Skor: **{skor}/100** — {status}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Total Kata Unik", total_unik)
        st.metric("✅ Kata Tuntas", f"{tuntas}/{total_unik}")
        st.metric("📝 Total Benar", f"{total_benar}/{target}")
    with col2:
        st.metric("❌ Total Salah", salah)
        st.metric("🔁 Total Percobaan", percobaan)
        st.metric("⭐ Kualitas (Akurasi)", f"{kualitas}%")

    if salah == 0:
        st.success("🌟 SEMPURNA! Tidak ada kesalahan sama sekali!")
    elif kualitas >= 80:
        st.success(f"💪 Akurasi tinggi! {kualitas}% jawaban benar.")
    elif kualitas >= 50:
        st.info(f"👍 Akurasi cukup. Butuh {percobaan} percobaan.")
    else:
        st.warning(f"💡 Akurasi rendah. Coba ulangi sesi ini!")

    if st.button("🚪 Kembali ke Menu Utama",
                 type="primary", use_container_width=True):
        reset_sesi()
        st.session_state.halaman = "menu"
        st.rerun()


# =========================================================
#  HALAMAN PEMAHAMAN
# =========================================================
def render_pemahaman():
    st.title("📖 MODE PEMAHAMAN 📖")
    st.caption(
        f"📚 Nomor {st.session_state.range_mulai}-{st.session_state.range_selesai} • "
        f"📄 {st.session_state.file_aktif}"
    )

    data = st.session_state.get("data_pemahaman", [])
    if not data:
        st.warning("Tidak ada data untuk ditampilkan.")
        if st.button("🚪 Kembali ke Menu"):
            st.session_state.halaman = "menu"
            st.rerun()
        return

    n_cols = st.slider("Jumlah kolom:", min_value=1, max_value=5, value=3)
    rows = [data[i:i + n_cols] for i in range(0, len(data), n_cols)]

    for row in rows:
        cols = st.columns(len(row))
        for col, kos in zip(cols, row):
            with col:
                with st.container(border=True):
                    st.caption(f"#{data.index(kos) + 1}")
                    if kos.get("huruf"):
                        st.markdown(f"### {kos['huruf']}")
                    st.markdown(f"**{kos['jepang']}**")
                    st.divider()
                    st.markdown(f"🔵 {kos['indo']}")

    st.divider()
    if st.button("🚪 Keluar ke Menu Utama", use_container_width=True):
        st.session_state.halaman = "menu"
        st.rerun()


# =========================================================
#  RESET SESI
# =========================================================
def reset_sesi():
    st.session_state.sesi_aktif = False
    st.session_state.sesi_kata_unik = []
    st.session_state.sesi_progress = {}
    st.session_state.sesi_total_salah = 0
    st.session_state.sesi_total_percobaan = 0
    st.session_state.sesi_total_benar_mentah = 0
    st.session_state.antrian_soal = []
    st.session_state.soal_sekarang = None
    st.session_state.sudah_dijawab = False
    st.session_state.pesan_feedback = None
    st.session_state.pilihan_jawaban = []


# =========================================================
#  MAIN
# =========================================================
def main():
    if st.session_state.file_aktif is None:
        files = daftar_file_tersimpan()
        if files:
            st.session_state.file_aktif = files[0]
            st.session_state.data_kosakata = muat_data(files[0])
        else:
            try:
                simpan_data("default.json", [])
            except Exception:
                pass
            st.session_state.file_aktif = "default.json"
            st.session_state.data_kosakata = []

    render_sidebar()

    if st.session_state.halaman == "menu":
        render_menu()
    elif st.session_state.halaman == "kuis":
        render_kuis()
    elif st.session_state.halaman == "pemahaman":
        render_pemahaman()


if __name__ == "__main__":
    main()
