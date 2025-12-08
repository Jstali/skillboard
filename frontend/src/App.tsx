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

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen pb-16 px-4">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <EmployeeDashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <EmployeeDashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/onboarding"
            element={
              <PrivateRoute>
                <OnboardingMapSkills />
              </PrivateRoute>
            }
          />
          <Route
            path="/edit-skills"
            element={
              <PrivateRoute>
                <OnboardingMapSkills />
              </PrivateRoute>
            }
          />
          <Route
            path="/skill-browser"
            element={
              <PrivateRoute>
                <OnboardingMapSkills />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <PrivateRoute>
                <AdminUsers />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/dashboard"
            element={
              <PrivateRoute>
                <AdminDashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/skill-gap"
            element={
              <PrivateRoute>
                <SkillGapBoard />
              </PrivateRoute>
            }
          />
          <Route
            path="/learning"
            element={
              <PrivateRoute>
                <EmployeeLearning />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/learning"
            element={
              <PrivateRoute>
                <AdminLearning />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/career-pathways"
            element={
              <PrivateRoute>
                <CareerPathways />
              </PrivateRoute>
            }
          />
          <Route
            path="/assignments"
            element={
              <PrivateRoute>
                <MyAssignments />
              </PrivateRoute>
            }
          />
          <Route
            path="/assignments/:assignmentId/fill"
            element={
              <PrivateRoute>
                <FillTemplate />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/template-assignment"
            element={
              <PrivateRoute>
                <TemplateAssignment />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/skill-gaps"
            element={
              <PrivateRoute>
                <SkillGapAnalysis />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/skill-gaps/:assignmentId/details"
            element={
              <PrivateRoute>
                <GapDetailsView />
              </PrivateRoute>
            }
          />
          <Route
            path="/"
            element={(() => {
              const user = authApi.getUser();
              // Redirect to dashboard (profile) as landing page
              if (!user) return <Navigate to="/login" replace />;
              const to = user.is_admin ? '/admin/dashboard' : '/dashboard';
              return <Navigate to={to} replace />;
            })()}
          />
        </Routes>
      </div>
      <footer className="fixed bottom-0 left-0 right-0 bg-[#F6F2F4] border-t border-gray-200 py-3 text-center text-xs text-gray-600 z-10">
        nxzen-skillboard@2025 All rights are reserved.
      </footer>
    </BrowserRouter>
  );
}

export default App;

