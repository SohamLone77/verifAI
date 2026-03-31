import React from 'react';
import { Menu, Bell, User, RefreshCw } from 'lucide-react';
import { useQueryClient } from 'react-query';
import toast from 'react-hot-toast';

const Header = ({ onMenuClick }) => {
  const queryClient = useQueryClient();

  const handleRefresh = async () => {
    await queryClient.invalidateQueries();
    toast.success('Data refreshed successfully');
  };

  return (
    <header className="sticky top-0 z-10 bg-white shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 lg:px-8">
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuClick}
            className="rounded-lg p-2 hover:bg-gray-100 lg:hidden"
          >
            <Menu className="h-5 w-5 text-gray-600" />
          </button>

          <div className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm">
              <img
                src="/verifai-logo.png"
                alt="VerifAI"
                className="h-6 w-6 object-contain"
              />
            </div>
            <h1 className="text-xl font-bold text-gray-800">VerifAI</h1>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
              v1.0
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefresh}
            className="rounded-lg p-2 hover:bg-gray-100"
            title="Refresh data"
          >
            <RefreshCw className="h-5 w-5 text-gray-600" />
          </button>

          <button className="relative rounded-lg p-2 hover:bg-gray-100">
            <Bell className="h-5 w-5 text-gray-600" />
            <span className="absolute right-1 top-1 flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500"></span>
            </span>
          </button>

          <button className="rounded-lg p-2 hover:bg-gray-100">
            <User className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
