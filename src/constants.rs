// version constants
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
pub const COMMIT: &str = env!("GIT_COMMIT_HASH");
pub const BUILD_DATE: &str = env!("BUILD_DATE");

#[cfg(not(target_os = "windows"))]
pub const COMPILE_C_LIB: &str = env!("C_LIB");
#[cfg(all(target_os = "windows", target_env = "msvc"))]
pub const COMPILE_C_LIB: &str = "msvc";
#[cfg(all(target_os = "windows", target_env = "gnu"))]
pub const COMPILE_C_LIB: &str = "gnu";
