import React, { useState } from 'react';
import { orgStructureApi, UploadResponse } from '../../services/api';

const OrgStructureUpload: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<UploadResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setResult(null);
            setError(null);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        try {
            setUploading(true);
            setError(null);
            const response = await orgStructureApi.uploadStructure(file);
            setResult(response);
            setFile(null);
            // Reset file input
            const fileInput = document.getElementById('file-upload') as HTMLInputElement;
            if (fileInput) fileInput.value = '';
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to upload file');
        } finally {
            setUploading(false);
        }
    };

    const downloadTemplate = () => {
        // Create a sample CSV template
        const csvContent = 'employee_id,manager_id,level\nEMP001,EMP002,2\nEMP003,EMP002,2\nEMP002,EMP004,1';
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'org_structure_template.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Organizational Structure Upload</h2>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-blue-900 mb-2">📋 Upload Instructions</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Upload an Excel (.xlsx) or CSV (.csv) file</li>
                    <li>• Required columns: <code className="bg-blue-100 px-1 rounded">employee_id</code>, <code className="bg-blue-100 px-1 rounded">manager_id</code></li>
                    <li>• Optional column: <code className="bg-blue-100 px-1 rounded">level</code> (organizational level)</li>
                    <li>• Employee IDs must match existing employees in the system</li>
                </ul>
                <button
                    onClick={downloadTemplate}
                    className="mt-3 text-blue-600 hover:text-blue-800 text-sm font-medium underline"
                >
                    Download Sample Template
                </button>
            </div>

            {error && (
                <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                    {error}
                    <button onClick={() => setError(null)} className="float-right font-bold">×</button>
                </div>
            )}

            {result && (
                <div className="mb-6 p-4 bg-green-100 border border-green-400 rounded">
                    <h3 className="font-semibold text-green-900 mb-2">✅ Upload Successful!</h3>
                    <div className="text-sm text-green-800">
                        <p><strong>Rows Processed:</strong> {result.rows_processed}</p>
                        {result.errors && result.errors.length > 0 && (
                            <div className="mt-3">
                                <p className="font-semibold text-red-700">Errors:</p>
                                <ul className="list-disc list-inside text-red-600 max-h-40 overflow-y-auto">
                                    {result.errors.map((err, idx) => (
                                        <li key={idx}>{err}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <form onSubmit={handleUpload}>
                    <div className="mb-6">
                        <label className="block text-gray-700 text-sm font-bold mb-2">
                            Select File
                        </label>
                        <input
                            id="file-upload"
                            type="file"
                            accept=".xlsx,.xls,.csv"
                            onChange={handleFileChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                        />
                        {file && (
                            <p className="mt-2 text-sm text-gray-600">
                                Selected: <span className="font-medium">{file.name}</span> ({(file.size / 1024).toFixed(2)} KB)
                            </p>
                        )}
                    </div>

                    <button
                        type="submit"
                        disabled={!file || uploading}
                        className={`w-full px-4 py-3 rounded-lg font-medium transition ${!file || uploading
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-blue-600 text-white hover:bg-blue-700'
                            }`}
                    >
                        {uploading ? 'Uploading...' : 'Upload Organizational Structure'}
                    </button>
                </form>
            </div>

            <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="font-semibold text-gray-800 mb-2">ℹ️ What happens after upload?</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Line manager relationships will be updated for all employees</li>
                    <li>• Organizational hierarchy levels will be set (if provided)</li>
                    <li>• Existing manager assignments will be overwritten</li>
                    <li>• Invalid employee IDs will be skipped and reported as errors</li>
                </ul>
            </div>
        </div>
    );
};

export default OrgStructureUpload;
