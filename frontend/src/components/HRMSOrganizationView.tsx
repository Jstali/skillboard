import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { RefreshCw, MapPin, Users, Briefcase, Building } from 'lucide-react';

interface Location {
  id: number;
  name: string;
}

interface DeliveryManager {
  id: number;
  name: string;
  email?: string;
  company_email?: string;
  location_id?: number;
  location_name?: string;
}

interface Project {
  project_id: number;
  project_name: string;
  status: string;
}

export const HRMSOrganizationView: React.FC = () => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [deliveryManagers, setDeliveryManagers] = useState<DeliveryManager[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'locations' | 'managers' | 'projects'>('locations');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [locRes, dmRes, projRes] = await Promise.all([
        api.get('/api/admin/hrms/locations').catch(() => ({ data: { locations: [] } })),
        api.get('/api/admin/hrms/delivery-managers').catch(() => ({ data: { delivery_managers: [] } })),
        api.get('/api/admin/hrms/projects').catch(() => ({ data: { projects: [] } })),
      ]);

      setLocations(locRes.data.locations || []);
      setDeliveryManagers(dmRes.data.delivery_managers || []);
      setProjects(projRes.data.projects || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load HRMS organization data');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'locations', label: 'Locations', icon: MapPin, count: locations.length },
    { id: 'managers', label: 'Delivery Managers', icon: Users, count: deliveryManagers.length },
    { id: 'projects', label: 'Projects', icon: Briefcase, count: projects.length },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading HRMS data...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-4 border-b flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Building className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">HRMS Organization Data</h2>
        </div>
        <button
          onClick={fetchAllData}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="m-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b">
        <div className="flex">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              <span className={`px-2 py-0.5 text-xs rounded-full ${
                activeTab === tab.id ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Locations Tab */}
        {activeTab === 'locations' && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              Locations are used to assign Delivery Managers to employees based on their work location.
            </p>
            {locations.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No locations found in HRMS.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {locations.map((location) => (
                  <div
                    key={location.id}
                    className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <MapPin className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{location.name}</h3>
                        <p className="text-xs text-gray-500">ID: {location.id}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Delivery Managers Tab */}
        {activeTab === 'managers' && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              Delivery Managers are assigned to employees based on their location. Every employee has one DM.
            </p>
            {deliveryManagers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No delivery managers found in HRMS.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {deliveryManagers.map((dm) => (
                      <tr key={dm.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-500">{dm.id}</td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{dm.name}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{dm.company_email || dm.email || '-'}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{dm.location_name || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              Projects from HRMS. Line Managers are assigned per project/client.
            </p>
            {projects.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No projects found in HRMS.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Project ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Project Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {projects.map((project) => (
                      <tr key={project.project_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-500">{project.project_id}</td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{project.project_name}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            project.status === 'Active' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {project.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Info Footer */}
      <div className="p-4 bg-gray-50 border-t text-xs text-gray-500">
        <p><strong>Organization Structure:</strong></p>
        <ul className="mt-1 list-disc list-inside">
          <li><strong>Delivery Manager (DM):</strong> Assigned based on employee's location - every employee has one DM</li>
          <li><strong>Line Manager (LM):</strong> Comes from the client/project - an employee can have multiple LMs</li>
          <li><strong>Capability Partner:</strong> Manages employees within a specific capability/skill area</li>
        </ul>
      </div>
    </div>
  );
};

export default HRMSOrganizationView;
