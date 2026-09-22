#include "bda_dialogs.h"
#include "bda_filesystem.h"

/* All mutations stay inside this example's dedicated FMAPI directory. */
static const char k_parent_path[] =
    "A:\\\xd3\xa6\xd3\xc3\\\xca\xfd\xbe\xdd\\\xd3\xce\xcf\xb7";
static const char k_test_dir[] =
    "A:\\\xd3\xa6\xd3\xc3\\\xca\xfd\xbe\xdd\\\xd3\xce\xcf\xb7\\FMAPI";
static const char k_old_path[] =
    "A:\\\xd3\xa6\xd3\xc3\\\xca\xfd\xbe\xdd\\\xd3\xce\xcf\xb7\\FMAPI\\OLD.TXT";
static const char k_new_path[] =
    "A:\\\xd3\xa6\xd3\xc3\\\xca\xfd\xbe\xdd\\\xd3\xce\xcf\xb7\\FMAPI\\NEW.TXT";
static const char k_log_path[] =
    "A:\\\xd3\xa6\xd3\xc3\\\xca\xfd\xbe\xdd\\\xd3\xce\xcf\xb7\\FMAPI.TXT";
static const char k_payload[] = "file-manager-api\r\n";

static char g_log[1024];
static char g_cwd[260];
static bda_fs_disk_info_t g_disk_info;
static bda_fs_path_info_t g_path_info;
static bda_fs_find_data_t g_find_data;

static char *append_char(char *out, char *end, char value) {
    if (out < end) {
        *out++ = value;
    }
    return out;
}

static char *append_text(char *out, char *end, const char *text) {
    while (*text != 0) {
        out = append_char(out, end, *text++);
    }
    return out;
}

static char *append_u32(char *out, char *end, u32 value) {
    char digits[10];
    int count = 0;

    do {
        digits[count++] = (char)('0' + value % 10u);
        value /= 10u;
    } while (value != 0u);
    while (count > 0) {
        out = append_char(out, end, digits[--count]);
    }
    return out;
}

static char *append_int(char *out, char *end, int value) {
    if (value < 0) {
        out = append_char(out, end, '-');
        return append_u32(out, end, 0u - (u32)value);
    }
    return append_u32(out, end, (u32)value);
}

static char *append_result(char *out, char *end, const char *name, int value) {
    out = append_text(out, end, name);
    out = append_char(out, end, '=');
    out = append_int(out, end, value);
    return append_char(out, end, '\n');
}

static int query_path(const char *path) {
    bda_fs_path_info_init(&g_path_info);
    return bda_fs_path_info(path, &g_path_info);
}

static int write_log(const char *text, bda_size_t size) {
    int file = bda_fs_fopen_raw(k_log_path, "wb");
    int written;

    if (!bda_fs_file_is_valid(file)) {
        return -1;
    }
    written = bda_fs_write_raw(file, text, size);
    (void)bda_fs_close_raw(file);
    bda_fs_flush_all();
    return written;
}

__attribute__((section(".text.bda_main")))
int bda_main(void) {
    char *out = g_log;
    char *end = g_log + sizeof(g_log) - 1;
    int failures = 0;
    int ready;
    int disk_result;
    int cwd_result;
    int mkdir_result;
    int directory_info;
    int directory_flag;
    int chdir_result;
    int file;
    int write_result = -1;
    int close_result = -1;
    int old_info;
    u32 old_size = 0;
    int find_result;
    int find_close = -1;
    int rename_result;
    int old_after_rename;
    int new_info;
    u32 new_size = 0;
    int chdir_parent;
    int rmdir_nonempty;
    int remove_result;
    int new_after_remove;
    int rmdir_empty;
    int directory_after_remove;
    int log_size;

    /* Clean only this example's names so the demo is repeatable. */
    (void)bda_fs_chdir(k_parent_path);
    (void)bda_fs_remove(k_old_path);
    (void)bda_fs_remove(k_new_path);
    (void)bda_fs_rmdir(k_test_dir);

    ready = bda_fs_storage_ready();
    bda_memset(&g_disk_info, 0, sizeof(g_disk_info));
    disk_result = bda_fs_disk_info(BDA_FS_DRIVE_A, &g_disk_info);
    bda_memset(g_cwd, 0, sizeof(g_cwd));
    cwd_result = bda_fs_getcwd(g_cwd, sizeof(g_cwd));

    mkdir_result = bda_fs_mkdir(k_test_dir);
    directory_info = query_path(k_test_dir);
    directory_flag = directory_info != -1
        ? bda_fs_path_info_is_dir(&g_path_info)
        : 0;
    chdir_result = bda_fs_chdir(k_test_dir);

    file = bda_fs_fopen_raw("OLD.TXT", "wb");
    if (bda_fs_file_is_valid(file)) {
        write_result = bda_fs_write_raw(file, k_payload, sizeof(k_payload) - 1u);
        close_result = bda_fs_close_raw(file);
    }

    old_info = query_path(k_old_path);
    if (old_info != -1) {
        old_size = g_path_info.size;
    }

    bda_fs_find_data_init(&g_find_data);
    find_result = bda_fs_findfirst("*.TXT", 0x27u, &g_find_data);
    if (find_result != -1) {
        find_close = bda_fs_findclose(&g_find_data);
    }

    rename_result = bda_fs_rename(k_old_path, k_new_path);
    old_after_rename = query_path(k_old_path);
    new_info = query_path(k_new_path);
    if (new_info != -1) {
        new_size = g_path_info.size;
    }

    chdir_parent = bda_fs_chdir(k_parent_path);
    rmdir_nonempty = bda_fs_rmdir(k_test_dir);
    remove_result = bda_fs_remove(k_new_path);
    new_after_remove = query_path(k_new_path);
    rmdir_empty = bda_fs_rmdir(k_test_dir);
    directory_after_remove = query_path(k_test_dir);

    if (ready == 0 || disk_result != 0 ||
        bda_fs_disk_total_bytes(&g_disk_info) == 0u ||
        bda_fs_disk_free_bytes(&g_disk_info) == 0u || cwd_result <= 0) failures++;
    if (mkdir_result == -1 || directory_info == -1 || !directory_flag ||
        chdir_result == -1) failures++;
    if (!bda_fs_file_is_valid(file) ||
        write_result != (int)(sizeof(k_payload) - 1u) || close_result == -1) failures++;
    if (old_info == -1 || old_size != sizeof(k_payload) - 1u ||
        find_result == -1 || find_close == -1) failures++;
    if (rename_result == -1 || old_after_rename != -1 ||
        new_info == -1 || new_size != sizeof(k_payload) - 1u) failures++;
    if (chdir_parent == -1 || rmdir_nonempty != -1) failures++;
    if (remove_result == -1 || new_after_remove != -1 ||
        rmdir_empty == -1 || directory_after_remove != -1) failures++;

    out = append_result(out, end, "storage_ready", ready);
    out = append_result(out, end, "disk0", disk_result);
    out = append_result(out, end, "bytes_per_sector", (int)g_disk_info.bytes_per_sector);
    out = append_result(out, end, "cwd_need", cwd_result);
    out = append_text(out, end, "cwd=");
    out = append_text(out, end, g_cwd);
    out = append_char(out, end, '\n');
    out = append_result(out, end, "mkdir", mkdir_result);
    out = append_result(out, end, "dir_info", directory_info);
    out = append_result(out, end, "dir_is_directory", directory_flag);
    out = append_result(out, end, "chdir", chdir_result);
    out = append_result(out, end, "write", write_result);
    out = append_result(out, end, "old_info", old_info);
    out = append_result(out, end, "old_size", (int)old_size);
    out = append_result(out, end, "findfirst", find_result);
    out = append_result(out, end, "rename", rename_result);
    out = append_result(out, end, "old_after_rename", old_after_rename);
    out = append_result(out, end, "new_info", new_info);
    out = append_result(out, end, "new_size", (int)new_size);
    out = append_result(out, end, "rmdir_nonempty", rmdir_nonempty);
    out = append_result(out, end, "remove", remove_result);
    out = append_result(out, end, "new_after_remove", new_after_remove);
    out = append_result(out, end, "rmdir_empty", rmdir_empty);
    out = append_result(out, end, "dir_after_rmdir", directory_after_remove);
    out = append_result(out, end, "failures", failures);
    out = append_text(out, end, failures == 0 ? "RESULT=PASS\n" : "RESULT=FAIL\n");
    *out = 0;

    log_size = (int)(out - g_log);
    if (write_log(g_log, (bda_size_t)log_size) != log_size) {
        bda_msgbox("FileManager API", "FAIL: result log write");
        return -1;
    }
    bda_msgbox(
        "FileManager API",
        failures == 0 ? "PASS: CRUD + metadata + disk" : "FAIL: export FMAPI.TXT"
    );
    return failures == 0 ? 0 : -1;
}
