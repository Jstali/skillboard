"""API routes for authentication."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import database, crud
from app.schemas import Token, UserLogin, UserRegister, UserResponse, PasswordChange
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.dependencies import get_current_active_user
from app.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(database.get_db),
):
    """Login endpoint - returns JWT token."""
    user = crud.get_user_by_email(db, email=user_credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            employee_id=user.employee_id,
            is_active=user.is_active,
            is_admin=user.is_admin,
            must_change_password=user.must_change_password,
            created_at=user.created_at,
            role_id=user.role_id,
        ),
    )


@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserRegister,
    db: Session = Depends(database.get_db),
):
    """Register endpoint - create new user account (optional, admin usually seeds)."""
    # Check if user already exists
    existing_user = crud.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if employee_id is provided and if user with that employee_id exists
    if user_data.employee_id:
        existing_employee_user = crud.get_user_by_employee_id(db, user_data.employee_id)
        if existing_employee_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already has an account",
            )
        
        # Create or update Employee record if employee_id is provided
        # Generate name from first_name/last_name or email
        name = f"{user_data.first_name} {user_data.last_name}".strip() if user_data.first_name and user_data.last_name else user_data.email.split("@")[0]
        crud.upsert_employee(
            db,
            employee_id=user_data.employee_id,
            name=name,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company_email=user_data.email,
            department=None,
            role=None,
        )
    
    # Create user
    password_hash = get_password_hash(user_data.password)
    user_dict = {
        "email": user_data.email,
        "password_hash": password_hash,
        "employee_id": user_data.employee_id,
        "is_active": True,
        "is_admin": False,
        "must_change_password": False,
    }
    
    user = crud.create_user(db, user_dict)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        employee_id=user.employee_id,
        is_active=user.is_active,
        is_admin=user.is_admin,
        must_change_password=user.must_change_password,
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        employee_id=current_user.employee_id,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        must_change_password=current_user.must_change_password,
        created_at=current_user.created_at,
        role_id=current_user.role_id,
    )


@router.post("/change-password", response_model=UserResponse)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Change user password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    # Update password
    new_password_hash = get_password_hash(password_data.new_password)
    updated_user = crud.update_user(
        db,
        current_user.id,
        {
            "password_hash": new_password_hash,
            "must_change_password": False,
        },
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        employee_id=updated_user.employee_id,
        is_active=updated_user.is_active,
        is_admin=updated_user.is_admin,
        must_change_password=updated_user.must_change_password,
        created_at=updated_user.created_at,
    )

