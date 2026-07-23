use std::sync::Mutex;
use memmap2::Mmap;
use std::fs::File;
use std::sync::OnceLock;

static MMAP_STATE: OnceLock<Mutex<Option<Mmap>>> = OnceLock::new();

fn get_state() -> &'static Mutex<Option<Mmap>> {
    MMAP_STATE.get_or_init(|| Mutex::new(None))
}

pub fn load_file(path: &str) -> Result<i64, String> {
    let file = File::open(path).map_err(|e| format!("Failed to open file: {}", e))?;
    let mmap = unsafe { Mmap::map(&file).map_err(|e| format!("Failed to create mmap: {}", e))? };
    let size = mmap.len() as i64;
    let mut state = get_state().lock().map_err(|e| format!("Lock poisoned: {}", e))?;
    *state = Some(mmap);
    Ok(size)
}

pub fn get_file_size() -> Result<i64, String> {
    let state = get_state().lock().map_err(|e| format!("Lock poisoned: {}", e))?;
    match state.as_ref() {
        Some(mmap) => Ok(mmap.len() as i64),
        None => Err("No file loaded".to_string()),
    }
}

pub fn unload_file() -> Result<(), String> {
    let mut state = get_state().lock().map_err(|e| format!("Lock poisoned: {}", e))?;
    *state = None;
    Ok(())
}

pub fn with_mmap<F, R>(f: F) -> Result<R, String>
where
    F: FnOnce(&[u8]) -> Result<R, String>,
{
    let state = get_state().lock().map_err(|e| format!("Lock poisoned: {}", e))?;
    match state.as_ref() {
        Some(mmap) => f(mmap),
        None => Err("No file loaded".to_string()),
    }
}
