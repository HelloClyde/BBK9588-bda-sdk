#include "../bda_research_sdk.h"

/*
 * Destructive filesystem probe for APIs needed by a file manager.
 * All mutations are restricted to the dedicated FMAPI directory/file names.
 */
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

static char g_log[1400];
static char g_cwd_before[260];
static char g_cwd_inside[260];
static bda_fs_path_info_like_t g_path_info;
static bda_fs_disk_info_like_t g_disk_info;
static bda_fs_find_data_like_t g_find_data;

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
    u32 magnitude;

    if (value < 0) {
        out = append_char(out, end, '-');
        magnitude = 0u - (u32)value;
    } else {
        magnitude = (u32)value;
    }
    return append_u32(out, end, magnitude);
}

static char *append_result(char *out, char *end, const char *name, int value) {
    out = append_text(out, end, name);
    out = append_char(out, end, '=');
    out = append_int(out, end, value);
    return append_char(out, end, '\n');
}

static char *append_value(char *out, char *end, const char *name, u32 value) {
    out = append_text(out, end, name);
    out = append_char(out, end, '=');
    out = append_u32(out, end, value);
    return append_char(out, end, '\n');
}

static int path_info(const char *path) {
    bda_fs_path_info_init_like(&g_path_info);
    return bda_fs_path_info_like(path, &g_path_info);
}

static int write_probe_log(const char *text, bda_size_t size) {
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
    int cwd_before_need;
    int mkdir_result;
    int dir_info_result;
    int dir_is_directory;
    int chdir_result;
    int cwd_inside_need;
    int file;
    int write_result = -1;
    int close_result = -1;
    int old_info_result;
    u32 old_size = 0;
    int find_result;
    int find_close_result = -1;
    int rename_result;
    int old_after_rename;
    int new_info_result;
    u32 new_size = 0;
    int chdir_parent_result;
    int rmdir_nonempty_result;
    int remove_result;
    int new_after_remove;
    int rmdir_empty_result;
    int dir_after_rmdir;
    int log_size;
    int log_write;

    /* Make repeated runs deterministic without touching unrelated paths. */
    (void)bda_fs_chdir_like(k_parent_path);
    (void)bda_fs_remove_raw(k_old_path);
    (void)bda_fs_remove_raw(k_new_path);
    (void)bda_fs_rmdir_like(k_test_dir);

    ready = bda_fs_storage_ready_like();
    bda_memset(&g_disk_info, 0, sizeof(g_disk_info));
    disk_result = bda_fs_diskinfo_like(0u, &g_disk_info);
    bda_memset(g_cwd_before, 0, sizeof(g_cwd_before));
    cwd_before_need = bda_fs_getcwd_like(g_cwd_before, sizeof(g_cwd_before));

    mkdir_result = bda_fs_mkdir_like(k_test_dir);
    dir_info_result = path_info(k_test_dir);
    dir_is_directory = dir_info_result != -1
        ? bda_fs_path_info_is_dir_like(&g_path_info)
        : 0;

    chdir_result = bda_fs_chdir_like(k_test_dir);
    bda_memset(g_cwd_inside, 0, sizeof(g_cwd_inside));
    cwd_inside_need = bda_fs_getcwd_like(g_cwd_inside, sizeof(g_cwd_inside));

    file = bda_fs_fopen_raw("OLD.TXT", "wb");
    if (bda_fs_file_is_valid(file)) {
        write_result = bda_fs_write_raw(file, k_payload, sizeof(k_payload) - 1u);
        close_result = bda_fs_close_raw(file);
    }

    old_info_result = path_info(k_old_path);
    if (old_info_result != -1) {
        old_size = bda_fs_path_info_size_like(&g_path_info);
    }

    bda_fs_find_data_init_like(&g_find_data);
    find_result = bda_fs_findfirst_like("*.TXT", 0x27u, &g_find_data);
    if (find_result != -1) {
        find_close_result = bda_fs_findclose_like(&g_find_data);
    }

    rename_result = bda_fs_rename_like(k_old_path, k_new_path);
    old_after_rename = path_info(k_old_path);
    new_info_result = path_info(k_new_path);
    if (new_info_result != -1) {
        new_size = bda_fs_path_info_size_like(&g_path_info);
    }

    chdir_parent_result = bda_fs_chdir_like(k_parent_path);
    rmdir_nonempty_result = bda_fs_rmdir_like(k_test_dir);
    remove_result = bda_fs_remove_raw(k_new_path);
    new_after_remove = path_info(k_new_path);
    rmdir_empty_result = bda_fs_rmdir_like(k_test_dir);
    dir_after_rmdir = path_info(k_test_dir);

    if (ready == 0 || disk_result != 0 || cwd_before_need <= 0) failures++;
    if (mkdir_result == -1 || dir_info_result == -1 || !dir_is_directory) failures++;
    if (chdir_result == -1 || cwd_inside_need <= 0) failures++;
    if (!bda_fs_file_is_valid(file) ||
        write_result != (int)(sizeof(k_payload) - 1u) || close_result == -1) failures++;
    if (old_info_result == -1 || old_size != sizeof(k_payload) - 1u) failures++;
    if (find_result == -1 || find_close_result == -1) failures++;
    if (rename_result == -1 || old_after_rename != -1 ||
        new_info_result == -1 || new_size != sizeof(k_payload) - 1u) failures++;
    if (chdir_parent_result == -1 || rmdir_nonempty_result != -1) failures++;
    if (remove_result == -1 || new_after_remove != -1) failures++;
    if (rmdir_empty_result == -1 || dir_after_rmdir != -1) failures++;

    out = append_result(out, end, "storage_ready", ready);
    out = append_result(out, end, "disk0", disk_result);
    out = append_value(out, end, "total_clusters", g_disk_info.total_clusters);
    out = append_value(out, end, "free_clusters", g_disk_info.free_clusters);
    out = append_value(out, end, "sectors_per_cluster", g_disk_info.sectors_per_cluster);
    out = append_value(out, end, "bytes_per_sector", g_disk_info.bytes_per_sector);
    out = append_result(out, end, "cwd_before_need", cwd_before_need);
    out = append_text(out, end, "cwd_before=");
    out = append_text(out, end, g_cwd_before);
    out = append_char(out, end, '\n');
    out = append_result(out, end, "mkdir", mkdir_result);
    out = append_result(out, end, "dir_info", dir_info_result);
    out = append_result(out, end, "dir_is_directory", dir_is_directory);
    out = append_result(out, end, "chdir", chdir_result);
    out = append_result(out, end, "cwd_inside_need", cwd_inside_need);
    out = append_text(out, end, "cwd_inside=");
    out = append_text(out, end, g_cwd_inside);
    out = append_char(out, end, '\n');
    out = append_result(out, end, "file_handle", file);
    out = append_result(out, end, "write", write_result);
    out = append_result(out, end, "close", close_result);
    out = append_result(out, end, "old_info", old_info_result);
    out = append_value(out, end, "old_size", old_size);
    out = append_result(out, end, "findfirst", find_result);
    out = append_result(out, end, "findclose", find_close_result);
    out = append_result(out, end, "rename", rename_result);
    out = append_result(out, end, "old_after_rename", old_after_rename);
    out = append_result(out, end, "new_info", new_info_result);
    out = append_value(out, end, "new_size", new_size);
    out = append_result(out, end, "chdir_parent", chdir_parent_result);
    out = append_result(out, end, "rmdir_nonempty", rmdir_nonempty_result);
    out = append_result(out, end, "remove", remove_result);
    out = append_result(out, end, "new_after_remove", new_after_remove);
    out = append_result(out, end, "rmdir_empty", rmdir_empty_result);
    out = append_result(out, end, "dir_after_rmdir", dir_after_rmdir);
    out = append_result(out, end, "failures", failures);
    out = append_text(out, end, failures == 0 ? "RESULT=PASS\n" : "RESULT=FAIL\n");
    *out = 0;

    log_size = (int)(out - g_log);
    log_write = write_probe_log(g_log, (bda_size_t)log_size);
    if (log_write != log_size) {
        bda_msgbox("FileManager API", "FAIL: result log write");
    } else if (failures == 0) {
        bda_msgbox("FileManager API", "PASS: CRUD + metadata + disk");
    } else {
        bda_msgbox("FileManager API", "FAIL: export FMAPI.TXT");
    }
    return failures == 0 && log_write == log_size ? 0 : -1;
}
