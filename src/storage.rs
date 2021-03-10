use rusqlite::{params};
use r2d2_sqlite::SqliteConnectionManager;

pub type DatabaseConnection = r2d2::PooledConnection<SqliteConnectionManager>;
pub type DatabaseConnectionPool = r2d2::Pool<SqliteConnectionManager>;

#[derive(Debug)]
pub struct DatabaseError;
impl warp::reject::Reject for DatabaseError { }

pub fn get_db_pool() -> DatabaseConnectionPool {
    let db_manager = SqliteConnectionManager::file("messages.db");
    return r2d2::Pool::new(db_manager).unwrap(); // Force
}

pub fn get_db_conn(db_pool: &DatabaseConnectionPool) -> Result<DatabaseConnection, warp::reject::Rejection> {
    match db_pool.get() {
        Ok(db_conn) => return Ok(db_conn),
        Err(e) => { 
            println!("Couldn't get database connection from pool due to error: {:?}.", e);
            return Err(warp::reject::custom(DatabaseError));
        }
    }
}

pub fn create_table_if_needed(db_conn: &DatabaseConnection) {
    // The `id` field is needed to make `rowid` stable
    db_conn.execute(
        "CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            text TEXT
        )",
        params![]
    ).expect("Couldn't create messages table.");
}