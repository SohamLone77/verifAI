import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
  Users,
  DollarSign,
  Settings,
  X,
} from 'lucide-react';
import { motion } from 'framer-motion';

const navigation = [
  { name: 'Dashboard', icon: LayoutDashboard, path: '/', color: 'text-blue-500' },
  { name: 'ROI Calculator', icon: TrendingUp, path: '/roi', color: 'text-green-500' },
  { name: 'Analytics', icon: BarChart3, path: '/analytics', color: 'text-purple-500' },
  { name: 'Agents', icon: Users, path: '/agents', color: 'text-indigo-500' },
  { name: 'Cost Tracking', icon: DollarSign, path: '/cost', color: 'text-orange-500' },
  { name: 'Settings', icon: Settings, path: '/settings', color: 'text-gray-500' },
];

const Sidebar = ({ onClose }) => {
  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b px-4">
        <div className="flex items-center space-x-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm">
            <img
              src="/verifai-logo.png"
              alt="VerifAI"
              className="h-6 w-6 object-contain"
            />
          </div>
          <span className="text-lg font-semibold text-gray-800">VerifAI</span>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1 hover:bg-gray-100 lg:hidden"
        >
          <X className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-2 py-4">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center space-x-3 rounded-lg px-3 py-2.5 transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 text-green-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`h-5 w-5 ${isActive ? item.color : 'text-gray-400'}`} />
                <span className="font-medium">{item.name}</span>
                {isActive && (
                  <motion.div
                    layoutId="active-indicator"
                    className="ml-auto h-1.5 w-1.5 rounded-full bg-green-500"
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t p-4">
        <div className="rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 p-3">
          <p className="text-xs font-medium text-green-800">Enterprise Ready</p>
          <p className="mt-1 text-xs text-green-600">Verify AI, One Output at a Time</p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
