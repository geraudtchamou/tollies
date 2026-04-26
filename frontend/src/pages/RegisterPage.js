import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { register, clearError } from '../../store/slices/authSlice';

const RegisterPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error } = useSelector((state) => state.auth);
  
  const [registerMethod, setRegisterMethod] = useState('email'); // 'email' or 'phone'
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    is_anonymous: false,
  });

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({ ...formData, [e.target.name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    dispatch(clearError());
    
    if (formData.password !== formData.confirm_password) {
      alert('Passwords do not match!');
      return;
    }

    try {
      const userData = {
        is_anonymous: formData.is_anonymous,
      };
      
      if (registerMethod === 'email') {
        userData.email = formData.email;
        userData.password = formData.password;
      } else {
        userData.phone = formData.phone;
        // Phone registration doesn't require password initially
      }
      
      await dispatch(register(userData)).unwrap();
      navigate('/login');
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Create Account</h1>
        <p style={styles.subtitle}>Join your community safety network</p>
        
        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.tabs}>
          <button
            style={{ ...styles.tab, ...(registerMethod === 'email' ? styles.activeTab : {}) }}
            onClick={() => setRegisterMethod('email')}
          >
            Email
          </button>
          <button
            style={{ ...styles.tab, ...(registerMethod === 'phone' ? styles.activeTab : {}) }}
            onClick={() => setRegisterMethod('phone')}
          >
            Phone
          </button>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          {registerMethod === 'email' ? (
            <>
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleChange}
                required={registerMethod === 'email'}
                style={styles.input}
              />
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                required={registerMethod === 'email'}
                style={styles.input}
              />
            </>
          ) : (
            <input
              type="tel"
              name="phone"
              placeholder="Phone (e.g., +1234567890)"
              value={formData.phone}
              onChange={handleChange}
              required={registerMethod === 'phone'}
              style={styles.input}
            />
          )}
          
          {registerMethod === 'email' && (
            <input
              type="password"
              name="confirm_password"
              placeholder="Confirm Password"
              value={formData.confirm_password}
              onChange={handleChange}
              required
              style={styles.input}
            />
          )}

          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              name="is_anonymous"
              checked={formData.is_anonymous}
              onChange={handleChange}
            />
            Register anonymously (your identity will be hidden)
          </label>

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <div style={styles.footer}>
          <p>
            Already have an account?{' '}
            <Link to="/login" style={styles.link}>Login</Link>
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
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    color: '#666',
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
};

export default RegisterPage;
