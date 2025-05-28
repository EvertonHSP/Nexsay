import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = () => {
  const { user, logout } = useAuth();

  return (
    <div>
      <nav className="navbar">
        <div>
          <Link to="/">Home</Link>
          {!user ? (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          ) : (
            <button onClick={logout}>Logout</button>
          )}
        </div>
      </nav>
      <div className="content-container">
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;