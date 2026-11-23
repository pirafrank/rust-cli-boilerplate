// version constants
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
pub const COMMIT: &str = env!("GIT_COMMIT_HASH");
pub const BUILD_DATE: &str = env!("BUILD_DATE");

/// C library the binary was built against, detected by `build.rs`.
pub const COMPILE_C_LIB: &str = env!("C_LIB");
