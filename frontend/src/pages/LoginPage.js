import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { login, register, requestOTP, verifyOTP, clearError } from '../../store/slices/authSlice';
import { getCurrentUser } from '../../store/slices/authSlice';

const LoginPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error } = useSelector((state) => state.auth);
  
  const [loginMethod, setLoginMethod] = useState('email'); // 'email' or 'phone'
  const [useOTP, setUseOTP] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    password: '',
    otp_code: '',
  });
  const [otpSent, setOtpSent] = useState(false);
  const [demoOtp, setDemoOtp] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    dispatch(clearError());
    
    try {
      await dispatch(login({ username: formData.email, password: formData.password })).unwrap();
      await dispatch(getCurrentUser()).unwrap();
      navigate('/');
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  const handlePhoneLogin = async (e) => {
    e.preventDefault();
    dispatch(clearError());
    
    if (useOTP) {
      if (!otpSent) {
        // Request OTP
        try {
          const result = await dispatch(requestOTP(formData.phone)).unwrap();
          setOtpSent(true);
          setDemoOtp(result.demo_otp);
        } catch (err) {
          console.error('OTP request failed:', err);
        }
      } else {
        // Verify OTP
        try {
          await dispatch(verifyOTP({ phone: formData.phone, otp_code: formData.otp_code })).unwrap();
          await dispatch(getCurrentUser()).unwrap();
          navigate('/');
        } catch (err) {
          console.error('OTP verification failed:', err);
        }
      }
    } else {
      // Password-based phone login
      try {
        await dispatch(login({ username: formData.phone, password: formData.password })).unwrap();
        await dispatch(getCurrentUser()).unwrap();
        navigate('/');
      } catch (err) {
        console.error('Login failed:', err);
      }
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Community Safety App</h1>
        <p style={styles.subtitle}>Stay informed, stay safe</p>
        
        {error && <div style={styles.error}>{error}</div>}
        
        {demoOtp && (
          <div style={styles.demoOtp}>
            Demo OTP: <strong>{demoOtp}</strong>
          </div>
        )}

        <div style={styles.tabs}>
          <button
            style={{ ...styles.tab, ...(loginMethod === 'email' ? styles.activeTab : {}) }}
            onClick={() => setLoginMethod('email')}
          >
            Email
          </button>
          <button
            style={{ ...styles.tab, ...(loginMethod === 'phone' ? styles.activeTab : {}) }}
            onClick={() => setLoginMethod('phone')}
          >
            Phone
          </button>
        </div>

        {loginMethod === 'email' ? (
          <form onSubmit={handleEmailLogin} style={styles.form}>
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              required
              style={styles.input}
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              style={styles.input}
            />
            <button type="submit" disabled={loading} style={styles.button}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        ) : (
          <form onSubmit={handlePhoneLogin} style={styles.form}>
            <input
              type="tel"
              name="phone"
              placeholder="Phone (e.g., +1234567890)"
              value={formData.phone}
              onChange={handleChange}
              required
              style={styles.input}
            />
            
            {!useOTP ? (
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                style={styles.input}
              />
            ) : (
              <>
                {!otpSent ? (
                  <button type="submit" disabled={loading} style={styles.button}>
                    {loading ? 'Sending OTP...' : 'Send OTP'}
                  </button>
                ) : (
                  <>
                    <input
                      type="text"
                      name="otp_code"
                      placeholder="Enter 6-digit OTP"
                      value={formData.otp_code}
                      onChange={handleChange}
                      maxLength="6"
                      required
                      style={styles.input}
                    />
                    <button type="submit" disabled={loading} style={styles.button}>
                      {loading ? 'Verifying...' : 'Verify & Login'}
                    </button>
                  </>
                )}
              </>
            )}
            
            {!useOTP && (
              <button type="submit" disabled={loading} style={styles.button}>
                {loading ? 'Logging in...' : 'Login'}
              </button>
            )}
          </form>
        )}

        {loginMethod === 'phone' && !useOTP && (
          <button
            onClick={() => setUseOTP(true)}
            style={styles.linkButton}
          >
            Login with OTP instead
          </button>
        )}

        {loginMethod === 'phone' && useOTP && otpSent && (
          <button
            onClick={() => { setUseOTP(false); setOtpSent(false); }}
            style={styles.linkButton}
          >
            Back to password login
          </button>
        )}

        <div style={styles.footer}>
          <p>
            Don't have an account?{' '}
            <Link to="/register" style={styles.link}>Register</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '20px',
  },
  card: {
    background: 'white',
    borderRadius: '16px',
    padding: '40px',
    width: '100%',
    maxWidth: '400px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: '8px',
    color: '#333',
  },
  subtitle: {
    textAlign: 'center',
    color: '#666',
    marginBottom: '30px',
  },
  tabs: {
    display: 'flex',
    marginBottom: '20px',
    borderBottom: '2px solid #eee',
  },
  tab: {
    flex: 1,
    padding: '12px',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    color: '#666',
    transition: 'all 0.3s',
  },
  activeTab: {
    color: '#667eea',
    borderBottom: '2px solid #667eea',
    marginBottom: '-2px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  input: {
    padding: '14px',
    border: '2px solid #eee',
    borderRadius: '8px',
    fontSize: '16px',
    transition: 'border-color 0.3s',
  },
  button: {
    padding: '14px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  },
  linkButton: {
    background: 'none',
    border: 'none',
    color: '#667eea',
    cursor: 'pointer',
    fontSize: '14px',
    marginTop: '12px',
    textDecoration: 'underline',
  },
  footer: {
    marginTop: '24px',
    textAlign: 'center',
    color: '#666',
  },
  link: {
    color: '#667eea',
    textDecoration: 'none',
    fontWeight: 'bold',
  },
  error: {
    background: '#fee',
    color: '#c00',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '16px',
    textAlign: 'center',
  },
  demoOtp: {
    background: '#e8f5e9',
    color: '#2e7d32',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '16px',
    textAlign: 'center',
  },
};

export default LoginPage;
