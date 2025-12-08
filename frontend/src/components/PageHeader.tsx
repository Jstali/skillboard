import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import NxzenLogo from '../images/Nxzen.jpg';

interface PageHeaderProps {
    title: string;
    subtitle?: string;
    rightAction?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, rightAction }) => {
    const navigate = useNavigate();
    const user = authApi.getUser();

    const handleLogout = () => {
        authApi.logout();
        navigate('/login');
    };

    return (
        <header className="bg-[#F6F2F4] shadow-sm border-b border-gray-200 -mx-4 mb-6">
            <div className="w-full px-4 py-4 flex flex-col sm:flex-row justify-between items-center gap-4">
                <div className="flex items-center gap-3">
                    <img src={NxzenLogo} alt="Nxzen" className="h-8 w-8 object-cover" />
                    <span className="text-xl font-semibold text-gray-800">nxzen</span>
                    <span aria-hidden className="hidden sm:block h-6 w-px bg-gray-300" />
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 italic" style={{ fontFamily: '"Times New Roman", Times, serif', fontStyle: 'italic' }}>
                            {title}
                        </h1>
                        {subtitle && <p className="text-xs text-gray-500 hidden sm:block">{subtitle}</p>}
                    </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto">
                    {rightAction}

                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-200 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-gray-700">
                            <path fillRule="evenodd" d="M12 2a5 5 0 100 10 5 5 0 000-10zm-7 18a7 7 0 1114 0H5z" clipRule="evenodd" />
                        </svg>
                        <div className="text-sm font-medium text-gray-800 text-right">
                            {((user as any)?.first_name && (user as any)?.last_name)
                                ? `${(user as any).first_name} ${(user as any).last_name}`
                                : (user?.employee_id || (user?.email ? user.email.split('@')[0] : 'User'))}
                            <br />
                            {user?.email && <span className="text-xs text-gray-500">{user.email}</span>}
                        </div>
                    </div>

                    <button
                        onClick={handleLogout}
                        title="Logout"
                        className="p-2 rounded-lg hover:bg-gray-200 text-red-600 transition-colors"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 transform rotate-180">
                            <path d="M16 13v-2H7V8l-5 4 5 4v-3h9zm3-11H9c-1.1 0-2 .9-2 2v3h2V4h10v16H9v-2H7v3c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                        </svg>
                    </button>
                </div>
            </div>
        </header>
    );
};
