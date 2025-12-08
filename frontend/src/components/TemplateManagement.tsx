/** Template Management Component for Skills Tab */
import React, { useState, useEffect, useRef } from 'react';
import { SearchableSelect } from './SearchableSelect';
import { api, templatesApi, SkillTemplate, TemplateUploadResponse } from '../services/api';

interface TemplateManagementProps {
    onUploadSuccess?: (result: TemplateUploadResponse) => void;
    onUploadError?: (error: string) => void;
}

export const TemplateManagement: React.FC<TemplateManagementProps> = ({
    onUploadSuccess,
    onUploadError,
}) => {
    const [templates, setTemplates] = useState<SkillTemplate[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<SkillTemplate | null>(null);
    const [showViewModal, setShowViewModal] = useState(false);
    const [templateToDelete, setTemplateToDelete] = useState<number | null>(null);
    const [editingContent, setEditingContent] = useState<any[][] | null>(null);
    const [saving, setSaving] = useState(false);

    // Rename state
    const [renamingId, setRenamingId] = useState<number | null>(null);
    const [renameValue, setRenameValue] = useState('');

    // Assignment state
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [assignTemplateId, setAssignTemplateId] = useState<number | null>(null);
    const [employees, setEmployees] = useState<any[]>([]);
    const [selectedEmployeeIds, setSelectedEmployeeIds] = useState<number[]>([]);
    const [assigning, setAssigning] = useState(false);
    const [userSelectionMode, setUserSelectionMode] = useState<'individual' | 'bulk'>('individual');
    const [selectedDepartment, setSelectedDepartment] = useState('');
    const [selectedRole, setSelectedRole] = useState('');

    // Sample Template State
    const [showSampleModal, setShowSampleModal] = useState(false);
    const [sampleTemplates, setSampleTemplates] = useState<{ template_name: string; content: any[][] }[]>([]);
    const [loadingSamples, setLoadingSamples] = useState(false);
    const [previewSample, setPreviewSample] = useState<{ template_name: string; content: any[][] } | null>(null);

    // Upload Name Prompt State
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadName, setUploadName] = useState('');
    const [showUploadNameModal, setShowUploadNameModal] = useState(false);

    const fileInputRef = useRef<HTMLInputElement | null>(null);

    useEffect(() => {
        loadTemplates();
        loadEmployees();
        loadSampleTemplates();
    }, []);

    const loadTemplates = async () => {
        console.log('DEBUG: loadTemplates called');
        setLoading(true);
        try {
            console.log('DEBUG: Calling templatesApi.getAll()...');
            const data = await templatesApi.getAll();
            console.log('DEBUG: Templates loaded successfully:', data);
            setTemplates(data);
        } catch (error: any) {
            console.error('DEBUG: Failed to load templates:', error);
            console.error('DEBUG: Error response:', error.response);
            onUploadError?.(error.response?.data?.detail || 'Failed to load templates');
        } finally {
            console.log('DEBUG: Setting loading to false');
            setLoading(false);
        }
    };

    const loadEmployees = async () => {
        try {
            // Fetch basic employee list for dropdown
            const response = await api.get('/api/admin/employees');
            console.log('DEBUG: Loaded employees:', response.data);
            if (response.data && response.data.length > 0) {
                console.log('DEBUG: First employee object:', response.data[0]);
                console.log('DEBUG: First employee id:', response.data[0].id);
                console.log('DEBUG: First employee employee_id:', response.data[0].employee_id);
            }
            setEmployees(response.data || []);
        } catch (error) {
            console.error("Failed to load employees for assignment", error);
        }
    };

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setUploadFile(file);
        // Default name from filename without extension, replace underscores with spaces
        const defaultName = file.name.split('.').slice(0, -1).join('.').replace(/_/g, ' ');
        setUploadName(defaultName);
        setShowUploadNameModal(true);

        // Reset input immediately
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleUploadConfirm = async () => {
        if (!uploadFile) {
            console.error('No file selected for upload');
            return;
        }

        console.log('Starting upload for file:', uploadFile.name, 'with name:', uploadName);
        setUploading(true);

        try {
            console.log('Calling templatesApi.upload...');
            const result = await templatesApi.upload(uploadFile, uploadName);
            console.log('Upload successful:', result);

            onUploadSuccess?.(result);
            await loadTemplates();
            setShowUploadNameModal(false);
            setUploadFile(null);
            setUploadName('');
        } catch (error: any) {
            console.error('Upload error:', error);
            console.error('Error response:', error.response);
            console.error('Error message:', error.message);

            const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload file';
            onUploadError?.(errorMessage);

            // Close modal on error to allow user to restart (especially if file invalid)
            setShowUploadNameModal(false);
            setUploadFile(null);
        } finally {
            console.log('Upload process completed, resetting uploading state');
            setUploading(false);
        }
    };

    const handleViewTemplate = async (templateId: number) => {
        try {
            const template = await templatesApi.getById(templateId);
            setSelectedTemplate(template);
            const content = JSON.parse(JSON.stringify(template.content || []));
            setEditingContent(content);
            setShowViewModal(true);
        } catch (error: any) {
            onUploadError?.(error.response?.data?.detail || 'Failed to load template content');
        }
    };

    const handleRenameStart = (template: SkillTemplate) => {
        setRenamingId(template.id);
        setRenameValue(template.template_name);
    };

    const handleRenameSave = async () => {
        if (!renamingId) return;
        try {
            await templatesApi.rename(renamingId, renameValue);
            setRenamingId(null);
            loadTemplates();
        } catch (error: any) {
            onUploadError?.(error.response?.data?.detail || 'Failed to rename template');
        }
    };



    const handleSaveChanges = async () => {
        if (!selectedTemplate || !editingContent) return;

        setSaving(true);
        try {
            const updatedTemplate = await templatesApi.update(selectedTemplate.id, editingContent);
            setSelectedTemplate(updatedTemplate);
            await loadTemplates();
            onUploadSuccess?.({
                message: 'Template updated successfully',
                rows_updated: updatedTemplate.row_count || 0
            } as any);
            // Don't close modal automatically, let user keep editing
        } catch (error: any) {
            onUploadError?.(error.response?.data?.detail || 'Failed to update template');
        } finally {
            setSaving(false);
        }
    };

    const handleDownloadSample = async (templateName?: string) => {
        try {
            const response = await api.get('/api/admin/templates/sample', {
                params: {
                    download: true,
                    template_name: templateName
                },
                responseType: 'blob'
            });

            // Create blob link to download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;

            // Set filename
            const cleanName = templateName ? templateName.replace(/_/g, ' ') : 'Skillboard_Sample_Templates_All';
            link.setAttribute('download', `${cleanName}.xlsx`);

            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error: any) {
            onUploadError?.(error.response?.data?.detail || 'Failed to download sample');
        }
    };

    // Unified Sample Loading
    const loadSampleTemplates = async () => {
        setLoadingSamples(true);
        try {
            const data = await templatesApi.getSample();
            setSampleTemplates(data);
        } catch (error: any) {
            console.error("Failed to load sample templates", error);
            // Don't show error to user immediately on load to avoid clutter, 
            // or maybe show a subtle toast if needed.
        } finally {
            setLoadingSamples(false);
        }
    };

    // Preview Handler (opens modal with specific sample)
    const handlePreviewSample = (sample: { template_name: string; content: any[][] }) => {
        setPreviewSample(sample);
        setShowSampleModal(true);
    };

    const handleUseSample = async (template: { template_name: string; content: any[][] }) => {
        setUploading(true);
        try {
            // Convert to CSV to leverage existing upload API
            const csvContent = template.content.map(row => row.map((cell: any) => `"${(cell || '').toString().replace(/"/g, '""')}"`).join(",")).join("\n");
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const cleanName = template.template_name.replace(/_/g, ' ');
            const file = new File([blob], `${cleanName}.csv`, { type: 'text/csv' });

            const result = await templatesApi.upload(file);
            onUploadSuccess?.(result);
            await loadTemplates();
        } catch (error: any) {
            onUploadError?.(error.response?.data?.detail || 'Failed to use sample template');
        } finally {
            setUploading(false);
            setShowSampleModal(false);
        }
    };

    // Editor Sample Picker State
    const [showSamplePicker, setShowSamplePicker] = useState(false);

    // Apply sample content to current editor
    const handleApplySample = (sample: { template_name: string; content: any[][] }) => {
        if (!editingContent) return;

        // Confirm overwrite
        if (confirm(`Replace current content with "${sample.template_name.replace(/_/g, ' ')}"? This cannot be undone.`)) {
            setEditingContent(JSON.parse(JSON.stringify(sample.content)));
            setShowSamplePicker(false);
        }
    };

    const handleOpenAssignModal = (id: number) => {
        setAssignTemplateId(id);
        setSelectedEmployeeIds([]);
        setUserSelectionMode('individual');
        setSelectedDepartment('');
        setSelectedRole('');
        setShowAssignModal(true);
    };

    const handleAssign = async () => {
        if (!assignTemplateId) return;

        console.log('DEBUG: handleAssign called');
        console.log('DEBUG: assignTemplateId:', assignTemplateId);
        console.log('DEBUG: userSelectionMode:', userSelectionMode);
        console.log('DEBUG: selectedEmployeeIds:', selectedEmployeeIds);
        console.log('DEBUG: selectedDepartment:', selectedDepartment);
        console.log('DEBUG: selectedRole:', selectedRole);

        setAssigning(true);
        try {
            let result;
            if (userSelectionMode === 'individual') {
                console.log('DEBUG: Calling templatesApi.assign with employee IDs:', selectedEmployeeIds);
                result = await templatesApi.assign(assignTemplateId, selectedEmployeeIds);
            } else {
                console.log('DEBUG: Calling templatesApi.assign with filters');
                result = await templatesApi.assign(assignTemplateId, [], {
                    department: selectedDepartment || undefined,
                    role: selectedRole || undefined
                });
            }

            console.log('DEBUG: Assignment result:', result);
            onUploadSuccess?.({ message: result.message } as any);
            if (result.errors && result.errors.length > 0) {
                onUploadError?.(`Assigned with errors: ${result.errors.join(', ')}`);
            }
            setShowAssignModal(false);
        } catch (error: any) {
            console.error('DEBUG: Assignment error:', error);
            onUploadError?.(error.response?.data?.detail || 'Failed to assign template');
        } finally {
            setAssigning(false);
        }
    };

    const handleDeleteTemplate = async (templateId: number) => {
        try {
            const result = await templatesApi.delete(templateId);
            onUploadSuccess?.({ message: result.message } as any);
            await loadTemplates();
            setTemplateToDelete(null);
        } catch (error: any) {
            onUploadError?.(error.response?.data?.detail || 'Failed to delete template');
            setTemplateToDelete(null);
        }
    };

    return (
        <>
            <div className="bg-white rounded-lg shadow-md p-6 mt-6">
                {/* Header */}
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-800">Template Files</h2>
                        <p className="text-sm text-gray-600 mt-1">
                            Upload spreadsheet files (.xlsx, .csv, .ods) to extract and store templates
                        </p>
                    </div>
                </div>
                {/* Action Buttons Row */}
                <div className="flex gap-4 mb-6">
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploading}
                        className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2 shadow-sm"
                    >
                        {uploading ? (
                            <>
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Uploading...
                            </>
                        ) : (
                            <>
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                                </svg>
                                Upload Template File
                            </>
                        )}
                    </button>
                </div>

                {/* Templates Header */}
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-700">All Templates</h3>
                    </div>
                </div>

                {/* Hidden Input for Uploads - Moved here for cleaner structure */}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.csv,.ods"
                    onChange={handleFileUpload}
                    className="hidden"
                />

                {/* Templates Table */}
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Template Name
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    File Name
                                </th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Rows
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Uploaded Date
                                </th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {/* Loading State */}
                            {(loading || loadingSamples) && templates.length === 0 && sampleTemplates.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                        Loading templates...
                                    </td>
                                </tr>
                            )}

                            {/* Empty State */}
                            {!loading && !loadingSamples && templates.length === 0 && sampleTemplates.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500 bg-gray-50">
                                        No templates found. Upload a file to get started.
                                    </td>
                                </tr>
                            )}

                            {/* Uploaded Templates */}
                            {templates.map((template) => (
                                <tr key={template.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {renamingId === template.id ? (
                                            <div className="flex items-center gap-2">
                                                <input
                                                    type="text"
                                                    value={renameValue}
                                                    onChange={(e) => setRenameValue(e.target.value)}
                                                    className="border border-blue-400 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                                                    autoFocus
                                                />
                                                <button onClick={handleRenameSave} className="text-green-600 hover:text-green-800"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg></button>
                                                <button onClick={() => setRenamingId(null)} className="text-red-500 hover:text-red-700"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-2 group">
                                                <span className="text-sm font-medium text-gray-900">{template.template_name.replace(/_/g, ' ')}</span>
                                                <button
                                                    onClick={() => handleRenameStart(template)}
                                                    className="text-gray-400 hover:text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    title="Rename"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" />
                                                    </svg>
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-600">{template.file_name}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <span className="text-sm text-gray-900">{template.row_count || 0}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-600">
                                            {new Date(template.created_at).toLocaleDateString('en-US', { dateStyle: 'medium' })}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <div className="flex items-center justify-center gap-2">
                                            <button
                                                onClick={() => handleOpenAssignModal(template.id)}
                                                className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100 text-sm font-medium border border-indigo-200"
                                            >
                                                Assign
                                            </button>
                                            <button
                                                onClick={() => handleViewTemplate(template.id)}
                                                className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
                                            >
                                                Edit / View
                                            </button>
                                            <button
                                                onClick={() => setTemplateToDelete(template.id)}
                                                className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded hover:bg-red-50 hover:text-red-600 text-sm font-medium transition-colors"
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Structured Web Page View Modal */}
            {
                showViewModal && selectedTemplate && editingContent && (
                    <div className="fixed inset-0 bg-gray-50 z-50 flex flex-col h-screen w-screen overflow-hidden">
                        {/* Top Bar - Template Name & Global Actions */}
                        <div className="px-8 py-5 bg-white border-b border-gray-200 flex justify-between items-center shadow-sm z-10">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => setShowViewModal(false)}
                                    className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition-colors"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
                                    </svg>
                                </button>
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                                        {selectedTemplate.template_name.replace(/_/g, ' ')}
                                        <span className="text-lg font-normal text-gray-400">
                                            {(editingContent.length - 1)} skills
                                        </span>
                                    </h2>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                {/* Removed: Add Category and Import Skills buttons */}
                                <button
                                    onClick={() => setShowSamplePicker(true)}
                                    className="px-5 py-2.5 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 font-medium shadow-sm transition-colors flex items-center gap-2"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                                    </svg>
                                    Templates
                                </button>
                                <button
                                    onClick={handleSaveChanges}
                                    disabled={saving}
                                    className="px-5 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-gray-900 font-medium shadow-sm transition-colors flex items-center gap-2"
                                >
                                    {saving ? (
                                        <>
                                            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Saving...
                                        </>
                                    ) : 'Save Changes'}
                                </button>
                            </div>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-auto bg-gray-50 p-8">
                            <div className="max-w-7xl mx-auto space-y-4">
                                {(() => {
                                    // Dynamic Grouping Logic
                                    // Find the header row by looking for key columns
                                    // Find the header row by looking for key columns with scoring
                                    const findHeaderRow = () => {
                                        let bestScore = -1;
                                        let bestIndex = 0;

                                        // Keywords to score against
                                        const keywords = ['skill', 'name', 'mandatory', 'beginner', 'intermediate', 'expert', 'developing', 'advanced'];

                                        for (let i = 0; i < Math.min(editingContent.length, 10); i++) {
                                            const rowStr = editingContent[i].join(' ').toLowerCase();
                                            let score = 0;

                                            keywords.forEach(kw => {
                                                if (rowStr.includes(kw)) score++;
                                            });

                                            if (score > bestScore) {
                                                bestScore = score;
                                                bestIndex = i;
                                            }
                                        }

                                        // If even the best score is 0 or 1 (likely just a title row), try to find a row with at least 2 matches
                                        // But if not found, we fallback to bestIndex which is likely 0
                                        return bestIndex;
                                    };

                                    const headerRowIndex = findHeaderRow();
                                    const headers = editingContent[headerRowIndex] || [];
                                    const categoryIndex = headers.findIndex(h => h?.toString().toLowerCase().includes('category'));

                                    // Group rows by category
                                    const groupedRows: Record<string, { row: any[], originalIndex: number }[]> = {};

                                    if (categoryIndex !== -1) {
                                        // Column-based grouping (Legacy/Explicit)
                                        editingContent.slice(headerRowIndex + 1).forEach((row, index) => {
                                            const category = row[categoryIndex] || 'Uncategorized';
                                            if (!groupedRows[category]) {
                                                groupedRows[category] = [];
                                            }
                                            groupedRows[category].push({ row, originalIndex: headerRowIndex + 1 + index });
                                        });
                                    } else {
                                        // Row-based Section grouping (New Scanner Logic)
                                        let currentSection = 'General Skills';
                                        let foundAnySection = false;

                                        // Check if the row immediately BEFORE the header row is a section header (e.g. "1. Core Skills")
                                        if (headerRowIndex > 0) {
                                            const prevRowFirstCell = editingContent[headerRowIndex - 1][0]?.toString().trim() || '';
                                            if (/^\d+\./.test(prevRowFirstCell) && prevRowFirstCell.length > 3) {
                                                currentSection = prevRowFirstCell;
                                                foundAnySection = true;
                                            }
                                        }

                                        // First pass: scan for numbered section headers
                                        const tempGroups: Record<string, { row: any[], originalIndex: number }[]> = {};

                                        editingContent.slice(headerRowIndex + 1).forEach((row, index) => {
                                            const firstCell = row[0]?.toString().trim() || '';
                                            const hasOtherContent = row.slice(1).some(cell => cell && cell.toString().trim() !== '');

                                            // Enhanced Section Header Detection
                                            // Detect various patterns:
                                            // 1. "1. Core Skills" or "2. Strategic Skills" (number + dot + text)
                                            // 2. "1" or "2" or "3" (just a number)
                                            // 3. "Core Skills" (text only in first column, rest empty)

                                            let isSectionHeader = false;

                                            // Pattern 1: Number followed by dot and text (e.g., "1. Agile & Delivery Practices")
                                            // This is a section header if it starts with a number and dot
                                            if (/^\d+\./.test(firstCell)) {
                                                // Check if it looks like a section header (has descriptive text after the number)
                                                const textAfterNumber = firstCell.replace(/^\d+\.\s*/, '');
                                                // If there's meaningful text after the number, it's likely a section header
                                                if (textAfterNumber.length > 3) {
                                                    isSectionHeader = true;
                                                }
                                            }
                                            // Pattern 2: Just a number (e.g., "1", "2", "3") with no other content
                                            else if (/^\d+$/.test(firstCell) && !hasOtherContent) {
                                                isSectionHeader = true;
                                            }
                                            // Pattern 3: Text in first column, but empty in all other columns (and text is substantial)
                                            else if (firstCell.length > 2 && !hasOtherContent && !/^\d+$/.test(firstCell)) {
                                                // Make sure it's not just a skill name by checking if it looks like a header
                                                // Headers are usually shorter and don't have colons or detailed descriptions
                                                if (firstCell.length < 50 && !firstCell.includes(':')) {
                                                    isSectionHeader = true;
                                                }
                                            }

                                            if (isSectionHeader) {
                                                currentSection = firstCell;
                                                foundAnySection = true;
                                                return; // Skip adding the header row itself as a skill
                                            }

                                            // Skip empty rows
                                            if (!row.some(cell => cell && cell.toString().trim() !== '')) return;

                                            if (!tempGroups[currentSection]) {
                                                tempGroups[currentSection] = [];
                                            }
                                            tempGroups[currentSection].push({ row, originalIndex: headerRowIndex + 1 + index });
                                        });

                                        // If no numbered sections were found, try to group by skill category from database
                                        if (!foundAnySection) {
                                            // Get skill name column index
                                            const skillIdx = headers.findIndex(h =>
                                                ['skill', 'name', 'title'].some(term => h?.toString().toLowerCase().includes(term))
                                            );

                                            if (skillIdx !== -1) {
                                                // Extract all skill names from the template
                                                const skillNames = editingContent.slice(headerRowIndex + 1)
                                                    .map(row => row[skillIdx]?.toString().trim())
                                                    .filter(name => name && name.length > 0);

                                                // Fetch skill categories from database (synchronously for now, could be optimized with caching)
                                                // We'll use the allSkills data if available, or create a category mapping
                                                const categoryMap: Record<string, string> = {};

                                                // Try to match skills with database to get their categories
                                                skillNames.forEach(skillName => {
                                                    // Simple case-insensitive matching
                                                    // In a real implementation, you might want to fetch this from the API
                                                    // For now, we'll extract category from skill name patterns or use a default

                                                    // Check if skill name contains common category indicators
                                                    const lowerName = skillName.toLowerCase();
                                                    if (lowerName.includes('hr') || lowerName.includes('human resource')) {
                                                        categoryMap[skillName] = 'HR Skills';
                                                    } else if (lowerName.includes('legal') || lowerName.includes('compliance') || lowerName.includes('regulatory')) {
                                                        categoryMap[skillName] = 'Legal & Compliance';
                                                    } else if (lowerName.includes('advisory') || lowerName.includes('negotiation') || lowerName.includes('client')) {
                                                        categoryMap[skillName] = 'Advisory & Negotiation';
                                                    } else if (lowerName.includes('risk') || lowerName.includes('management')) {
                                                        categoryMap[skillName] = 'Risk Management';
                                                    } else if (lowerName.includes('technology') || lowerName.includes('analytics') || lowerName.includes('data')) {
                                                        categoryMap[skillName] = 'Technology & Analytics';
                                                    } else if (lowerName.includes('strategic') || lowerName.includes('planning')) {
                                                        categoryMap[skillName] = 'Strategic Planning';
                                                    } else if (lowerName.includes('communication') || lowerName.includes('presentation')) {
                                                        categoryMap[skillName] = 'Communication Skills';
                                                    } else if (lowerName.includes('leadership') || lowerName.includes('team')) {
                                                        categoryMap[skillName] = 'Leadership & Team Management';
                                                    } else {
                                                        categoryMap[skillName] = 'General Skills';
                                                    }
                                                });

                                                // Regroup by detected categories
                                                const categoryGroups: Record<string, { row: any[], originalIndex: number }[]> = {};

                                                editingContent.slice(headerRowIndex + 1).forEach((row, index) => {
                                                    // Skip empty rows
                                                    if (!row.some(cell => cell && cell.toString().trim() !== '')) return;

                                                    const skillName = row[skillIdx]?.toString().trim() || '';
                                                    const category = categoryMap[skillName] || 'General Skills';

                                                    if (!categoryGroups[category]) {
                                                        categoryGroups[category] = [];
                                                    }
                                                    categoryGroups[category].push({ row, originalIndex: headerRowIndex + 1 + index });
                                                });

                                                // Use category groups instead of temp groups
                                                Object.assign(groupedRows, categoryGroups);
                                            } else {
                                                // Fallback to original groups if we can't find skill column
                                                Object.assign(groupedRows, tempGroups);
                                            }
                                        } else {
                                            // Use the numbered section groups
                                            Object.assign(groupedRows, tempGroups);
                                        }
                                    }

                                    return Object.entries(groupedRows).sort(([a], [b]) => {
                                        // Sort by the number prefix if present (e.g. "1. ..." comes before "2. ...")
                                        const numA = parseInt(a.match(/^\d+/)?.[0] || '999');
                                        const numB = parseInt(b.match(/^\d+/)?.[0] || '999');
                                        return numA - numB;
                                    }).map(([category, rows]) => (
                                        <div key={category} className="bg-white rounded border border-gray-100 shadow-sm overflow-hidden">
                                            {/* Category Header Row - Matches Screenshot Style */}
                                            <div className="px-6 py-4 bg-white flex justify-between items-center group">
                                                <h3 className="text-base font-bold text-gray-800">{category}</h3>

                                                <div className="flex items-center gap-4">
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            // Add a new row with this category pre-filled
                                                            const newRow = new Array(headers.length).fill('');
                                                            if (categoryIndex !== -1) newRow[categoryIndex] = category;
                                                            setEditingContent([...editingContent, newRow]);
                                                        }}
                                                        className="px-3 py-1.5 bg-green-500 text-white rounded hover:bg-green-600 text-sm font-medium transition-colors flex items-center gap-1"
                                                    >
                                                        + Add Skill
                                                    </button>

                                                    <div className="flex items-center gap-2 text-gray-400 min-w-[80px] justify-end cursor-pointer"
                                                        onClick={(e) => {
                                                            const contentDiv = document.getElementById(`content-${category}`);
                                                            if (contentDiv) {
                                                                contentDiv.classList.toggle('hidden');
                                                                e.currentTarget.querySelector('svg')?.classList.toggle('rotate-180');
                                                            }
                                                        }}>
                                                        <span className="text-sm">{rows.length} skills</span>
                                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 transition-transform">
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                                                        </svg>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Collapsible Content - Specific Table Layout */}
                                            <div id={`content-${category}`} className="hidden border-t border-gray-100 bg-white">
                                                {/* Table Helper to map columns securely */}
                                                {(() => {
                                                    const getColIndex = (searchTerms: string[]) =>
                                                        headers.findIndex(h => searchTerms.some(term => h?.toString().toLowerCase().includes(term)));

                                                    // Calculate indexes for other known columns first
                                                    const knownCols = {
                                                        desc: getColIndex(['desc', 'about', 'detail']),
                                                        mandatory: getColIndex(['mandatory', 'required']),
                                                        employees: getColIndex(['employee', 'count', 'target']),
                                                        beginner: getColIndex(['beginner', 'basic']),
                                                        developing: getColIndex(['developing']),
                                                        intermediate: getColIndex(['intermediate']),
                                                        advanced: getColIndex(['advanced']),
                                                        expert: getColIndex(['expert'])
                                                    };

                                                    // Smart Skill Column Detection
                                                    let skillIdx = getColIndex(['skill', 'name', 'title']);

                                                    if (skillIdx === -1) {
                                                        // Content Heuristic: Scan first 20 rows
                                                        // We look for a column (0 or 1) that has text, is NOT mapped to another column, and is NOT just numbers
                                                        const occupied = new Set(Object.values(knownCols).filter(i => i !== -1));
                                                        const sampleRows = editingContent.slice(headerRowIndex + 1, headerRowIndex + 20);

                                                        let bestCol = 0;
                                                        let maxScore = -1;

                                                        // Check first 3 columns as candidates
                                                        for (let c = 0; c < 3; c++) {
                                                            if (occupied.has(c)) continue;

                                                            let score = 0;
                                                            sampleRows.forEach(row => {
                                                                const val = row[c]?.toString().trim();
                                                                if (val) {
                                                                    // Boost score for text length > 3 (likely words)
                                                                    if (val.length > 3) score += 2;
                                                                    // Penalize or ignore purely numeric values (likely indices)
                                                                    else if (!isNaN(Number(val))) score -= 1;
                                                                    else score += 1;
                                                                }
                                                            });

                                                            if (score > maxScore) {
                                                                maxScore = score;
                                                                bestCol = c;
                                                            }
                                                        }
                                                        skillIdx = bestCol;
                                                    }

                                                    const idxMap = {
                                                        skill: skillIdx,
                                                        ...knownCols
                                                    };

                                                    return (
                                                        <table className="w-full text-left border-collapse">
                                                            <thead>
                                                                <tr className="text-[10px] text-gray-400 font-bold uppercase tracking-wider border-b border-gray-100">
                                                                    <th className="px-6 py-4 font-bold w-1/4">Skill</th>
                                                                    <th className="px-2 py-4 text-center">Mandatory</th>
                                                                    {idxMap.employees !== -1 && <th className="px-2 py-4 text-center">Employees</th>}
                                                                    <th className="px-4 py-4 text-center min-w-[100px]">A</th>
                                                                    <th className="px-4 py-4 text-center min-w-[100px]">B</th>
                                                                    <th className="px-4 py-4 text-center min-w-[100px]">C</th>
                                                                    <th className="px-4 py-4 text-center min-w-[100px]">L1</th>
                                                                    <th className="px-4 py-4 text-center min-w-[100px]">L2</th>
                                                                    <th className="px-4 py-4 w-10"></th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-gray-50">
                                                                {rows.map(({ row, originalIndex }) => (
                                                                    <tr key={originalIndex} className="hover:bg-gray-50/50 group transition-colors">
                                                                        {/* Skill Name & Description */}
                                                                        <td className="px-6 py-4">
                                                                            <div className="space-y-1">
                                                                                <input
                                                                                    type="text"
                                                                                    value={idxMap.skill !== -1 ? (row[idxMap.skill] || '') : ''}
                                                                                    onChange={(e) => {
                                                                                        if (idxMap.skill === -1) return;
                                                                                        const newContent = [...editingContent];
                                                                                        newContent[originalIndex][idxMap.skill] = e.target.value;
                                                                                        setEditingContent(newContent);
                                                                                    }}
                                                                                    className="block w-full text-sm font-semibold text-gray-900 bg-transparent border-none p-0 focus:ring-0 placeholder-gray-300"
                                                                                    placeholder="Skill Name"
                                                                                />
                                                                                <input
                                                                                    type="text"
                                                                                    value={idxMap.desc !== -1 ? (row[idxMap.desc] || '') : ''}
                                                                                    onChange={(e) => {
                                                                                        if (idxMap.desc === -1) return;
                                                                                        const newContent = [...editingContent];
                                                                                        newContent[originalIndex][idxMap.desc] = e.target.value;
                                                                                        setEditingContent(newContent);
                                                                                    }}
                                                                                    className="block w-full text-xs text-gray-400 bg-transparent border-none p-0 focus:ring-0 placeholder-gray-200"
                                                                                    placeholder="Add description..."
                                                                                />
                                                                            </div>
                                                                        </td>

                                                                        {/* Mandatory Checkbox */}
                                                                        <td className="px-2 py-4 text-center">
                                                                            <input
                                                                                type="checkbox"
                                                                                checked={idxMap.mandatory !== -1 ? (row[idxMap.mandatory]?.toString().toLowerCase() === 'yes' || row[idxMap.mandatory] === true) : false}
                                                                                onChange={(e) => {
                                                                                    if (idxMap.mandatory === -1) return;
                                                                                    const newContent = [...editingContent];
                                                                                    newContent[originalIndex][idxMap.mandatory] = e.target.checked ? 'Yes' : 'No';
                                                                                    setEditingContent(newContent);
                                                                                }}
                                                                                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500 h-4 w-4"
                                                                            />
                                                                        </td>

                                                                        {/* Band Level Columns */}
                                                                        {['employees', 'beginner', 'developing', 'intermediate', 'advanced', 'expert'].map((colKey) => {
                                                                            const colIdx = idxMap[colKey as keyof typeof idxMap];
                                                                            if (colKey === 'employees' && colIdx === -1) return null; // Hide employees if not present

                                                                            // For band columns (not employees), use dropdown
                                                                            const isBandColumn = colKey !== 'employees';

                                                                            return (
                                                                                <td key={colKey} className="px-2 py-4 text-center">
                                                                                    {isBandColumn ? (
                                                                                        <select
                                                                                            value={colIdx !== -1 ? (row[colIdx] || '') : ''}
                                                                                            onChange={(e) => {
                                                                                                if (colIdx === -1) return;
                                                                                                const newContent = [...editingContent];
                                                                                                newContent[originalIndex][colIdx] = e.target.value;
                                                                                                setEditingContent(newContent);
                                                                                            }}
                                                                                            className="w-full text-center text-sm font-medium bg-white border border-gray-200 hover:border-gray-300 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded px-2 py-1 transition-colors"
                                                                                        >
                                                                                            <option value="">-</option>
                                                                                            <option value="Beginner">Beginner</option>
                                                                                            <option value="Developing">Developing</option>
                                                                                            <option value="Intermediate">Intermediate</option>
                                                                                            <option value="Advanced">Advanced</option>
                                                                                            <option value="Expert">Expert</option>
                                                                                        </select>
                                                                                    ) : (
                                                                                        <input
                                                                                            type="text"
                                                                                            value={colIdx !== -1 ? (row[colIdx] || '0') : '-'}
                                                                                            onChange={(e) => {
                                                                                                if (colIdx === -1) return;
                                                                                                const newContent = [...editingContent];
                                                                                                newContent[originalIndex][colIdx] = e.target.value;
                                                                                                setEditingContent(newContent);
                                                                                            }}
                                                                                            className="w-16 text-center text-sm font-medium bg-transparent border-transparent hover:border-gray-200 focus:border-green-500 rounded px-1 py-0.5 transition-colors text-gray-600"
                                                                                        />
                                                                                    )}
                                                                                </td>
                                                                            );
                                                                        })}

                                                                        {/* Delete Action */}
                                                                        <td className="px-4 py-4 text-right">
                                                                            <button
                                                                                onClick={() => {
                                                                                    const newContent = [...editingContent];
                                                                                    newContent.splice(originalIndex, 1);
                                                                                    setEditingContent(newContent);
                                                                                }}
                                                                                className="text-gray-300 hover:text-red-500 transition-colors p-1 opacity-0 group-hover:opacity-100"
                                                                                title="Delete Skill"
                                                                            >
                                                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                                                                </svg>
                                                                            </button>
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    );
                                                })()}
                                            </div>
                                        </div>
                                    ));
                                })()}
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Assignment Modal */}
            {
                showAssignModal && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
                            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                                <h3 className="text-lg font-bold text-gray-800">Assign Template</h3>
                                <p className="text-sm text-gray-500">Select employees to assign this skill template to.</p>
                            </div>

                            {/* Tabs */}
                            <div className="flex border-b border-gray-200">
                                <button
                                    onClick={() => setUserSelectionMode('individual')}
                                    className={`flex-1 py-3 text-sm font-medium ${userSelectionMode === 'individual' ? 'text-purple-600 border-b-2 border-purple-600' : 'text-gray-500 hover:text-gray-700'}`}
                                >
                                    Individual Employees
                                </button>
                                <button
                                    onClick={() => setUserSelectionMode('bulk')}
                                    className={`flex-1 py-3 text-sm font-medium ${userSelectionMode === 'bulk' ? 'text-purple-600 border-b-2 border-purple-600' : 'text-gray-500 hover:text-gray-700'}`}
                                >
                                    Bulk Assign (Role/Dept)
                                </button>
                            </div>

                            <div className="p-6 flex-1 overflow-auto">
                                {userSelectionMode === 'individual' ? (
                                    <>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Select Employees</label>
                                        <div className="border border-gray-200 rounded-lg max-h-60 overflow-y-auto divide-y divide-gray-100">
                                            {employees.map(emp => (
                                                <div key={emp.employee_id} className="flex items-center px-4 py-3 hover:bg-gray-50">
                                                    <input
                                                        type="checkbox"
                                                        id={`emp-${emp.employee_id}`}
                                                        checked={selectedEmployeeIds.includes(emp.id)} // id is db id, employee_id is string ID
                                                        onChange={(e) => {
                                                            console.log('DEBUG: Checkbox changed for employee:', emp);
                                                            console.log('DEBUG: emp.id:', emp.id);
                                                            console.log('DEBUG: e.target.checked:', e.target.checked);
                                                            if (e.target.checked) {
                                                                const newIds = [...selectedEmployeeIds, emp.id];
                                                                console.log('DEBUG: Adding employee, new selectedEmployeeIds:', newIds);
                                                                setSelectedEmployeeIds(newIds);
                                                            } else {
                                                                const newIds = selectedEmployeeIds.filter(id => id !== emp.id);
                                                                console.log('DEBUG: Removing employee, new selectedEmployeeIds:', newIds);
                                                                setSelectedEmployeeIds(newIds);
                                                            }
                                                        }}
                                                        className="h-4 w-4 text-purple-600 rounded border-gray-300 focus:ring-purple-500"
                                                    />
                                                    <label htmlFor={`emp-${emp.employee_id}`} className="ml-3 flex-1 cursor-pointer">
                                                        <span className="block text-sm font-medium text-gray-900">{emp.name}</span>
                                                        <span className="block text-xs text-gray-500">{emp.role} • {emp.department}</span>
                                                    </label>
                                                </div>
                                            ))}
                                            {employees.length === 0 && (
                                                <div className="p-4 text-center text-gray-500 text-sm">No employees found.</div>
                                            )}
                                        </div>
                                        <div className="mt-2 text-right text-xs text-gray-500">
                                            {selectedEmployeeIds.length} employees selected
                                        </div>
                                    </>
                                ) : (
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">By Department</label>
                                            <SearchableSelect
                                                options={Array.from(new Set(employees.map(e => e.department).filter(Boolean))).map(dept => ({ value: dept!, label: dept! }))}
                                                value={selectedDepartment}
                                                onChange={(v) => setSelectedDepartment(v as string)}
                                                placeholder="Select Department..."
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">By Job Role</label>
                                            <SearchableSelect
                                                options={Array.from(new Set(employees.map(e => e.role).filter(Boolean))).map(role => ({ value: role!, label: role! }))}
                                                value={selectedRole}
                                                onChange={(v) => setSelectedRole(v as string)}
                                                placeholder="Select Role..."
                                            />
                                        </div>
                                        <div className="p-3 bg-blue-50 text-blue-700 text-sm rounded-lg">
                                            This will assign the template to all current employees matching the selected criteria.
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                                <button
                                    onClick={() => setShowAssignModal(false)}
                                    className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAssign}
                                    disabled={assigning || (userSelectionMode === 'individual' && selectedEmployeeIds.length === 0) || (userSelectionMode === 'bulk' && !selectedDepartment && !selectedRole)}
                                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium text-sm disabled:opacity-50"
                                >
                                    {assigning ? 'Assigning...' : 'Confirm Assignment'}
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Delete Confirmation Modal */}
            {
                templateToDelete !== null && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
                            <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                                <h2 className="text-xl font-semibold text-white">Confirm Deletion</h2>
                            </div>
                            <div className="p-6">
                                <p className="text-gray-700">
                                    Are you sure you want to delete this template? This action cannot be undone.
                                </p>
                                <p className="text-sm text-gray-600 mt-2">
                                    Template: <span className="font-semibold">
                                        {templates.find(t => t.id === templateToDelete)?.template_name.replace(/_/g, ' ')}
                                    </span>
                                </p>
                            </div>
                            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                                <button
                                    onClick={() => setTemplateToDelete(null)}
                                    className="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => handleDeleteTemplate(templateToDelete)}
                                    className="px-5 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
            {/* Sample Templates Modal */}
            {
                showSampleModal && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-[90vh] overflow-hidden flex flex-col">
                            <div className="px-8 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                                <div>
                                    <h3 className="text-xl font-bold text-gray-800">Sample Templates</h3>
                                    <p className="text-sm text-gray-500">Preview and use standard templates or download the Excel file.</p>
                                </div>
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => handleDownloadSample()}
                                        className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium text-sm flex items-center gap-2 opacity-50 hover:opacity-100 transition-opacity"
                                        title="Download Full Sample File (All Sheets)"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                                        </svg>
                                        Full Excel File
                                    </button>
                                    <button
                                        onClick={() => setShowSampleModal(false)}
                                        className="p-2 rounded-full hover:bg-gray-200 text-gray-500 transition-colors"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                </div>
                            </div>

                            <div className="flex flex-1 overflow-hidden">
                                {/* Sidebar - List of Templates */}
                                <div className="w-64 border-r border-gray-200 bg-gray-50 overflow-y-auto">
                                    {loadingSamples ? (
                                        <div className="p-8 text-center text-gray-400">Loading...</div>
                                    ) : (
                                        <div className="p-4 space-y-2">
                                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">Available Templates</div>
                                            {sampleTemplates.map((template, idx) => (
                                                <button
                                                    key={idx}
                                                    onClick={() => setPreviewSample(template)}
                                                    className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${previewSample?.template_name === template.template_name ? 'bg-white text-purple-700 shadow-sm border border-gray-100 ring-1 ring-purple-500/10' : 'text-gray-600 hover:bg-white hover:text-gray-900'}`}
                                                >
                                                    {template.template_name.replace(/_/g, ' ')}
                                                    <span className="block text-xs font-normal text-gray-400 mt-0.5">{template.content.length - 1} rows</span>
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Preview Area */}
                                <div className="flex-1 bg-white flex flex-col overflow-hidden">
                                    {previewSample ? (
                                        <>
                                            <div className="p-4 border-b border-gray-100 bg-white flex justify-between items-center">
                                                <h4 className="font-bold text-gray-800">{previewSample.template_name.replace(/_/g, ' ')} <span className="text-gray-400 font-normal">Preview</span></h4>
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleDownloadSample(previewSample.template_name)}
                                                        className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 text-sm font-medium flex items-center gap-2"
                                                    >
                                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                                                        </svg>
                                                        Download
                                                    </button>
                                                    <button
                                                        onClick={() => handleUseSample(previewSample)}
                                                        className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm font-medium flex items-center gap-2"
                                                    >
                                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                                                        </svg>
                                                        Use This Template
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="flex-1 overflow-auto p-6 bg-gray-50/50">
                                                <div className="bg-white border border-gray-200 shadow-sm rounded-lg overflow-hidden">
                                                    <table className="min-w-full divide-y divide-gray-200">
                                                        <thead className="bg-gray-50">
                                                            <tr>
                                                                {previewSample.content[0]?.map((header: any, idx: number) => (
                                                                    <th key={idx} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap bg-gray-50 border-r border-gray-100 last:border-0 sticky top-0">
                                                                        {header}
                                                                    </th>
                                                                ))}
                                                            </tr>
                                                        </thead>
                                                        <tbody className="bg-white divide-y divide-gray-200">
                                                            {previewSample.content.slice(1).map((row: any[], rIdx: number) => (
                                                                <tr key={rIdx} className="hover:bg-gray-50">
                                                                    {row.map((cell: any, cIdx: number) => (
                                                                        <td key={cIdx} className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap border-r border-gray-100 last:border-0 max-w-xs truncate">
                                                                            {cell}
                                                                        </td>
                                                                    ))}
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex-1 flex items-center justify-center text-gray-400">
                                            Select a template from the list to preview
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Editor Sample Picker Modal */}
            {
                showSamplePicker && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[60] p-4">
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh]">
                            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                                <div>
                                    <h3 className="text-lg font-bold text-gray-800">Select Template</h3>
                                    <p className="text-xs text-gray-500">Choose a template to download or apply to the current editor.</p>
                                </div>
                                <button
                                    onClick={() => setShowSamplePicker(false)}
                                    className="p-1 rounded-full hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            <div className="p-4 overflow-y-auto space-y-2">
                                {sampleTemplates.map((template, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-4 bg-white border border-gray-100 rounded-lg hover:border-purple-200 hover:shadow-sm transition-all group">
                                        <div className="flex-1">
                                            <h4 className="text-sm font-semibold text-gray-900">{template.template_name.replace(/_/g, ' ')}</h4>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-xs px-2 py-0.5 bg-green-50 text-green-700 rounded border border-green-100">Standard</span>
                                                <span className="text-xs text-gray-400">{template.content.length - 1} rows</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleDownloadSample(template.template_name)}
                                                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                title="Download Excel File"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                                                </svg>
                                            </button>
                                            <button
                                                onClick={() => handleApplySample(template)}
                                                className="px-3 py-1.5 bg-purple-600 text-white text-xs font-medium rounded hover:bg-purple-700 transition-colors flex items-center gap-1 shadow-sm"
                                            >
                                                Use Template
                                            </button>
                                        </div>
                                    </div>
                                ))}
                                {sampleTemplates.length === 0 && (
                                    <div className="text-center py-8 text-gray-400 text-sm">No sample templates available.</div>
                                )}
                            </div>
                        </div>
                    </div>
                )
            }
            {/* Upload Name Modal */}
            {showUploadNameModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                        <h3 className="text-xl font-bold text-gray-800 mb-4">Name Your Template</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            Please provide a name for this template. This name will be used to identify it in the system.
                        </p>

                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Template Name</label>
                            <input
                                type="text"
                                value={uploadName}
                                onChange={(e) => setUploadName(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="e.g. Engineering Skills"
                                autoFocus
                            />
                        </div>

                        <div className="flex justify-end gap-3 transition-colors">
                            <button
                                onClick={() => {
                                    setShowUploadNameModal(false);
                                    setUploadFile(null);
                                }}
                                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
                                disabled={uploading}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleUploadConfirm}
                                disabled={!uploadName.trim() || uploading}
                                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
                            >
                                {uploading && (
                                    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                )}
                                Upload
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

