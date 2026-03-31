import bcrypt
from app.database import SessionLocal
from app import models

def get_password_hash(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_admin():
    db = SessionLocal()
    
    # Configurações do Admin
    admin_username = "admin"
    admin_password = "sua_senha_aqui" # Altere para sua senha desejada
    
    # Verifica se já existe
    existing_user = db.query(models.User).filter(models.User.username == admin_username).first()
    if existing_user:
        print(f"O usuário '{admin_username}' já existe no banco de dados.")
        db.close()
        return

    # Cria o hash da senha
    hashed_password = get_password_hash(admin_password)
    
    # Cria o novo usuário
    new_user = models.User(
        username=admin_username,
        hashed_password=hashed_password,
        is_admin=True,
        show_projects=True
    )
    
    try:
        db.add(new_user)
        db.commit()
        print(f"✅ Usuário administrador '{admin_username}' criado com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar usuário: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
    print("\n--- Script Finalizado ---")
