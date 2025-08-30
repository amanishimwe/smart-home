import { useState, useEffect } from 'react';
import authService from './services/auth';
function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    rememberMe: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [user, setUser] = useState(null);

  // Check for existing user on component mount
  useEffect(() => {
    const existingUser = authService.getUser();
    if (existingUser) {
      setUser(existingUser);
    }
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (isLogin) {
        // Login
        const response = await authService.login(
          formData.username,
          formData.password,
          formData.rememberMe
        );
        setUser(response.user);
        console.log('Login successful:', response);
      } else {
        // Register
        const response = await authService.register(
          formData.username,
          formData.email,
          formData.password
        );
        setSuccess('Registration successful! You can now login with your credentials.');
        console.log('Registration successful:', response);

        // Clear form after successful registration
        setFormData({
          username: '',
          password: '',
          email: '',
          rememberMe: false
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setFormData({
      username: '',
      password: '',
      email: '',
      rememberMe: false
    });
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setSuccess('');
    setFormData({
      username: '',
      password: '',
      email: '',
      rememberMe: false
    });
  };

  // If user is logged in, show dashboard
  if (user) {
    return (
      <section className="min-h-screen w-full flex items-center justify-center font-mono bg-gradient-to-r from-cyan-500 from-10% via-indigo-500 via-50% to-sky-500 to-100%">
        <div className="flex flex-col items-center justify-center text-center p-20 gap-8 bg-white rounded-2xl text-gray-900 shadow-2xl">
          {/* Welcome Message */}
          <h1 className="text-4xl font-bold">
            Welcome, {user.username}!
          </h1>

          <div className="flex flex-col gap-4 text-left">
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Role:</strong> {user.role}</p>
            <p><strong>Member since:</strong> {new Date(user.created_at).toLocaleDateString()}</p>
          </div>

          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-600 text-white p-3 rounded-md transition-colors text-base font-medium"
          >
            Logout
          </button>
        </div>
      </section>
    );
  }

  // Login/Register Form
  return (
    <section className="min-h-screen w-full flex items-center justify-center font-mono bg-gradient-to-r from-cyan-500 from-10% via-indigo-500 via-50% to-sky-500 to-100%">
      <div className="flex flex-col items-center justify-center text-center p-20 gap-8 bg-white rounded-2xl text-gray-900 shadow-2xl">
        {/* Header */}
        <h1 className="text-2xl font-bold">
          Welcome to the Smart Home
        </h1>

        {/* Error Message */}
        {error && (
          <div className="w-full max-w-md p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="w-full max-w-md p-3 bg-green-100 border border-green-400 text-green-700 rounded-md">
            {success}
            <div className="mt-3">
              <button
                type="button"
                onClick={toggleMode}
                className="text-green-700 hover:text-green-800 underline font-medium"
              >
                Click here to login
              </button>
            </div>
          </div>
        )}

        {/* Form */}
        {!success && (
          <form onSubmit={handleSubmit} className="flex flex-col text-2xl text-left gap-6 w-full max-w-md">
            {/* Username Input */}
            <input
              type="text"
              name="username"
              placeholder="Username"
              value={formData.username}
              onChange={handleInputChange}
              className="w-full p-3 rounded-md border border-gray-300 text-gray-900 text-base"
              required
            />

            {/* Email Input (only for register) */}
            {!isLogin && (
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleInputChange}
                className="w-full p-3 rounded-md border border-gray-300 text-gray-900 text-base"
                required
              />
            )}

            {/* Password Input */}
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleInputChange}
              className="w-full p-3 rounded-md border border-gray-300 text-gray-900 text-base"
              required
            />

            {/* Remember Me Checkbox (only for login) */}
            {isLogin && (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="rememberMe"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="rememberMe" className="text-sm text-gray-700">
                  Remember me
                </label>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="px-10 py-2 text-2xl rounded-md bg-gradient-to-tr from-green-400 to-blue-500 hover:from-pink-500 hover:to-yellow-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? 'Loading...' : (isLogin ? 'Login' : 'Register')}
            </button>

            {/* Toggle Mode Link */}
            <div className="text-center text-sm text-gray-600">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <button
                type="button"
                onClick={toggleMode}
                className="text-blue-500 hover:text-blue-600 underline ml-1 font-medium"
              >
                {isLogin ? 'Register' : 'Login'}
              </button>
            </div>
          </form>
        )}
      </div>
    </section>
  )
}

export default App
