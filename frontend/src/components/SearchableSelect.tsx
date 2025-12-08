import React, { useState, useEffect, useRef } from 'react';

interface Option {
    value: string | number;
    label: string;
}

interface SearchableSelectProps {
    options: Option[];
    value: string | number | null;
    onChange: (value: string | number) => void;
    placeholder?: string;
    className?: string;
    loading?: boolean;
    disabled?: boolean;
}

export const SearchableSelect: React.FC<SearchableSelectProps> = ({
    options,
    value,
    onChange,
    placeholder = 'Select...',
    className = '',
    loading = false,
    disabled = false,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filteredOptions, setFilteredOptions] = useState<Option[]>(options);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setFilteredOptions(
            options.filter((option) =>
                option.label.toLowerCase().includes(searchTerm.toLowerCase())
            )
        );
    }, [searchTerm, options]);

    useEffect(() => {
        // Close dropdown when clicking outside
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (option: Option) => {
        onChange(option.value);
        setIsOpen(false);
        setSearchTerm('');
    };

    const selectedOption = options.find((o) => o.value === value);

    return (
        <div className={`relative ${className}`} ref={wrapperRef}>
            <div
                className={`w-full px-3 py-2 bg-white border border-gray-300 rounded-lg flex items-center justify-between cursor-pointer focus:ring-2 focus:ring-blue-500 focus:outline-none ${disabled ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                onClick={() => !disabled && setIsOpen(!isOpen)}
            >
                <span className={`block truncate ${!selectedOption ? 'text-gray-400' : 'text-gray-900'}`}>
                    {selectedOption ? selectedOption.label : placeholder}
                </span>
                <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </div>

            {isOpen && !disabled && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-hidden flex flex-col">
                    <div className="p-2 border-b border-gray-100">
                        <input
                            type="text"
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded focus:outline-none focus:border-blue-500"
                            placeholder="Search..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            autoFocus
                        />
                    </div>

                    <div className="overflow-y-auto flex-1">
                        {loading ? (
                            <div className="px-4 py-2 text-sm text-gray-500 text-center">Loading...</div>
                        ) : filteredOptions.length === 0 ? (
                            <div className="px-4 py-2 text-sm text-gray-500 text-center">No options found</div>
                        ) : (
                            filteredOptions.map((option) => (
                                <div
                                    key={option.value}
                                    className={`px-4 py-2 text-sm cursor-pointer hover:bg-blue-50 ${option.value === value ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'
                                        }`}
                                    onClick={() => handleSelect(option)}
                                >
                                    {option.label}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
