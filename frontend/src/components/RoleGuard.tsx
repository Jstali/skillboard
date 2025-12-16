import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, Role } from '../contexts/AuthContext';

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles?: Role[];
  minRoleLevel?: number;
  fallback?: ReactNode;
  redirectTo?: string;
}

/**
 * RoleGuard - Protects routes and UI elements based on user role
 * 
 * Usage:
 * <RoleGuard allowedRoles={[Role.HR, Role.SYSTEM_ADMIN]}>
 *   <SensitiveComponent />
 * </RoleGuard>
 */
export const RoleGuard: React.FC<RoleGuardProps> = ({
  children,
  allowedRoles,
  minRoleLevel,
  fallback = null,
  redirectTo,
}) => {
  const { isAuthenticated, hasRole, hasMinRoleLevel } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const hasAccess = allowedRoles 
    ? hasRole(...allowedRoles)
    : minRoleLevel 
      ? hasMinRoleLevel(minRoleLevel)
      : true;

  if (!hasAccess) {
    if (redirectTo) {
      return <Navigate to={redirectTo} replace />;
    }
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

/**
 * RoleVisible - Conditionally renders UI based on role (no redirect)
 */
export const RoleVisible: React.FC<{ roles: Role[]; children: ReactNode }> = ({ roles, children }) => {
  const { hasRole } = useAuth();
  return hasRole(...roles) ? <>{children}</> : null;
};

/**
 * Hook for conditional rendering based on role
 */
export const useRoleAccess = () => {
  const { user, hasRole, hasMinRoleLevel } = useAuth();
  
  return {
    isAdmin: hasRole(Role.SYSTEM_ADMIN),
    isHR: hasRole(Role.HR, Role.SYSTEM_ADMIN),
    isManager: hasRole(Role.LINE_MANAGER, Role.DELIVERY_MANAGER, Role.HR, Role.SYSTEM_ADMIN),
    isCP: hasRole(Role.CAPABILITY_PARTNER),
    canViewSensitive: hasRole(Role.HR, Role.SYSTEM_ADMIN),
    canViewReports: hasRole(Role.LINE_MANAGER, Role.DELIVERY_MANAGER, Role.HR, Role.SYSTEM_ADMIN),
    canViewCapability: hasRole(Role.CAPABILITY_PARTNER, Role.HR, Role.SYSTEM_ADMIN),
    userRole: user?.role,
    userCapability: user?.capability,
  };
};
