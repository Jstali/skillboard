/** Main App component with routing. */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { EmployeeDashboard } from './pages/EmployeeDashboard';
import { OnboardingMapSkills } from './pages/OnboardingMapSkills';
import { AdminUsers } from './pages/AdminUsers';
import { AdminDashboard } from './pages/AdminDashboard';
import { SkillGapBoard } from './pages/SkillGapBoard';
import { EmployeeLearning } from './pages/EmployeeLearning';
import { AdminLearning } from './pages/AdminLearning';
import { CareerPathways } from './pages/CareerPathways';
import TemplateAssignment from './pages/TemplateAssignment';
import SkillGapAnalysis from './pages/SkillGapAnalysis';
import GapDetailsView from './pages/GapDetailsView';
import MyAssignments from './pages/MyAssignments';
import FillTemplate from './pages/FillTemplate';
import { PrivateRoute } from './components/PrivateRoute';
import { authApi } from './services/api';

// Role-based Dashboards
import HRDashboard from './pages/HRDashboard';
import LMDashboard from './pages/LMDashboard';
import CPDashboard from './pages/CPDashboard';
import DMDashboard from './pages/DMDashboard';

// HRMS Pre-Integration Components
import ProjectsManagement from './pages/admin/ProjectsManagement';
import CapabilityOwners from './pages/admin/CapabilityOwners';
import OrgStructureUpload from './pages/admin/OrgStructureUpload';
import LevelMovementApprovals from './pages/admin/LevelMovementApprovals';
import ReconciliationPlaceholder from './pages/admin/ReconciliationPlaceholder';
import HRMSTestPage from './pages/HRMSTestPage';


function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen pb-16 px-4">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Role-based Dashboards */}
          <Route path="/hr/dashboard" element={<PrivateRoute><AdminDashboard /></PrivateRoute>} />
          <Route path="/lm/dashboard" element={<PrivateRoute><LMDashboard /></PrivateRoute>} />
          <Route path="/cp/dashboard" element={<PrivateRoute><CPDashboard /></PrivateRoute>} />
          <Route path="/dm/dashboard" element={<PrivateRoute><DMDashboard /></PrivateRoute>} />
          
          {/* Employee Dashboard */}
          <Route path="/dashboard" element={<PrivateRoute><EmployeeDashboard /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><EmployeeDashboard /></PrivateRoute>} />
          
          {/* Common Routes */}
          <Route path="/onboarding" element={<PrivateRoute><OnboardingMapSkills /></PrivateRoute>} />
          <Route path="/edit-skills" element={<PrivateRoute><OnboardingMapSkills /></PrivateRoute>} />
          <Route path="/skill-browser" element={<PrivateRoute><OnboardingMapSkills /></PrivateRoute>} />
          <Route path="/skill-gap" element={<PrivateRoute><SkillGapBoard /></PrivateRoute>} />
          <Route path="/learning" element={<PrivateRoute><EmployeeLearning /></PrivateRoute>} />
          <Route path="/assignments" element={<PrivateRoute><MyAssignments /></PrivateRoute>} />
          <Route path="/assignments/:assignmentId/fill" element={<PrivateRoute><FillTemplate /></PrivateRoute>} />
          
          {/* Admin Routes */}
          <Route path="/admin/dashboard" element={<PrivateRoute><AdminDashboard /></PrivateRoute>} />
          <Route path="/admin/users" element={<PrivateRoute><AdminUsers /></PrivateRoute>} />
          <Route path="/admin/learning" element={<PrivateRoute><AdminLearning /></PrivateRoute>} />
          <Route path="/admin/career-pathways" element={<PrivateRoute><CareerPathways /></PrivateRoute>} />
          <Route path="/admin/template-assignment" element={<PrivateRoute><TemplateAssignment /></PrivateRoute>} />
          <Route path="/admin/skill-gaps" element={<PrivateRoute><SkillGapAnalysis /></PrivateRoute>} />
          <Route path="/admin/skill-gaps/:assignmentId/details" element={<PrivateRoute><GapDetailsView /></PrivateRoute>} />

          {/* HRMS Test Routes */}
          <Route path="/test/hrms" element={<PrivateRoute><HRMSTestPage /></PrivateRoute>} />
          <Route path="/test/projects" element={<PrivateRoute><ProjectsManagement /></PrivateRoute>} />
          <Route path="/test/capability-owners" element={<PrivateRoute><CapabilityOwners /></PrivateRoute>} />
          <Route path="/test/org-structure" element={<PrivateRoute><OrgStructureUpload /></PrivateRoute>} />
          <Route path="/test/level-movement" element={<PrivateRoute><LevelMovementApprovals /></PrivateRoute>} />
          <Route path="/test/reconciliation" element={<PrivateRoute><ReconciliationPlaceholder /></PrivateRoute>} />

          {/* Default redirect based on role */}
          <Route path="/" element={<RoleBasedRedirect />} />
        </Routes>
      </div>
      <footer className="fixed bottom-0 left-0 right-0 bg-[#F6F2F4] border-t border-gray-200 py-3 text-center text-xs text-gray-600 z-10">
        nxzen-skillboard@2025 All rights are reserved.
      </footer>
    </BrowserRouter>
  );
}

// Role-based redirect component
const RoleBasedRedirect: React.FC = () => {
  const user = authApi.getUser();
  if (!user) return <Navigate to="/login" replace />;
  
  switch (user.role_id) {
    case 1: return <Navigate to="/admin/dashboard" replace />;
    case 2: return <Navigate to="/hr/dashboard" replace />;
    case 3: return <Navigate to="/cp/dashboard" replace />;
    case 4: return <Navigate to="/dm/dashboard" replace />;
    case 5: return <Navigate to="/lm/dashboard" replace />;
    default: return <Navigate to="/dashboard" replace />;
  }
};

export default App;
