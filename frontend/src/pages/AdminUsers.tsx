/** Admin page for importing users and employee skill mappings. */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminApi, authApi, UploadResponse } from '../services/api';

export const AdminUsers: React.FC = () => {
  const [usersFile, setUsersFile] = useState<File | null>(null);
  const [skillsFile, setSkillsFile] = useState<File | null>(null);
  const [uploadingUsers, setUploadingUsers] = useState(false);
  const [uploadingSkills, setUploadingSkills] = useState(false);
  const [usersResult, setUsersResult] = useState<UploadResponse | null>(null);
  const [skillsResult, setSkillsResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const user = authApi.getUser();
  const [profileOpen, setProfileOpen] = useState(false);

  const handleUsersUpload = async () => {
    if (!usersFile) {
      setError('Please select a users CSV file');
      return;
    }

    setUploadingUsers(true);
    setError('');
    setUsersResult(null);

    try {
      const result = await adminApi.importUsers(usersFile);
      setUsersResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload users file');
    } finally {
      setUploadingUsers(false);
    }
  };

  const handleSkillsUpload = async () => {
    if (!skillsFile) {
      setError('Please select an employee skills CSV file');
      return;
    }

    setUploadingSkills(true);
    setError('');
    setSkillsResult(null);

    try {
      const result = await adminApi.importEmployeeSkills(skillsFile);
      setSkillsResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload skills file');
    } finally {
      setUploadingSkills(false);
    }
  };

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-[#F6F2F4]">
      <header className="bg-[#F6F2F4] shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-800">Admin - User Management</h1>
            <div className="ml-6 flex items-center gap-2">
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Dashboard
              </button>
            </div>
          </div>
          <div className="relative flex items-center">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-200"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-gray-700">
                <path fillRule="evenodd" d="M12 2a5 5 0 100 10 5 5 0 000-10zm-7 18a7 7 0 1114 0H5z" clipRule="evenodd" />
              </svg>
              <span className="text-sm font-medium text-gray-800">
                {((user as any)?.first_name && (user as any)?.last_name)
                  ? `${(user as any).first_name} ${(user as any).last_name}`
                  : (user?.employee_id || (user?.email ? user.email.split('@')[0] : 'User'))}
              </span>
              <span className="text-xs text-gray-500">({user?.email})</span>
            </button>
            {profileOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-red-600">
                    <path d="M16 13v-2H7V8l-5 4 5 4v-3h9zm3-11H9c-1.1 0-2 .9-2 2v3h2V4h10v16H9v-2H7v3c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                  </svg>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Users Import */}
          <div className="bg-[#F6F2F4] rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Import Users</h2>
            <p className="text-sm text-gray-600 mb-4">
              Upload a CSV file with columns: employee_id, first_name, last_name, company_email, department, role
            </p>
            <div className="mb-4">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setUsersFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <button
              onClick={handleUsersUpload}
              disabled={!usersFile || uploadingUsers}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploadingUsers ? 'Uploading...' : 'Upload Users'}
            </button>
            {usersResult && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <p className="text-sm font-semibold text-green-800">{usersResult.message}</p>
                <p className="text-xs text-green-600 mt-2">
                  Processed: {usersResult.rows_processed} | 
                  Created: {usersResult.rows_created} | 
                  Updated: {usersResult.rows_updated}
                </p>
                {usersResult.errors && usersResult.errors.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-red-600">Errors:</p>
                    <ul className="text-xs text-red-600 list-disc list-inside">
                      {usersResult.errors.slice(0, 5).map((err, idx) => (
                        <li key={idx}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Employee Skills Import */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Import Employee Skills</h2>
            <p className="text-sm text-gray-600 mb-4">
              Upload a CSV file with columns: employee_id, skill_name, rating, years_experience (optional), notes (optional)
            </p>
            <div className="mb-4">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setSkillsFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <button
              onClick={handleSkillsUpload}
              disabled={!skillsFile || uploadingSkills}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploadingSkills ? 'Uploading...' : 'Upload Skills'}
            </button>
            {skillsResult && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <p className="text-sm font-semibold text-green-800">{skillsResult.message}</p>
                <p className="text-xs text-green-600 mt-2">
                  Processed: {skillsResult.rows_processed} | 
                  Created: {skillsResult.rows_created} | 
                  Updated: {skillsResult.rows_updated}
                </p>
                {skillsResult.errors && skillsResult.errors.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-red-600">Errors:</p>
                    <ul className="text-xs text-red-600 list-disc list-inside">
                      {skillsResult.errors.slice(0, 5).map((err, idx) => (
                        <li key={idx}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-800 mb-2">CSV Format Requirements</h3>
          <div className="text-sm text-yellow-700 space-y-2">
            <p><strong>users.csv:</strong> employee_id, first_name, last_name, company_email, department, role</p>
            <p><strong>employee_skill_mappings.csv:</strong> employee_id, skill_name, rating, years_experience (optional), notes (optional)</p>
            <p className="mt-2 text-xs">Note: Rating values should be: Beginner, Developing, Intermediate, Advanced, or Expert</p>
          </div>
        </div>
      </div>
    </div>
  );
};

