import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaRoute, FaExclamationTriangle } from 'react-icons/fa';
import './LandingPage.css';

const LandingPage = () => {
  const canvasRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let particles = [];

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Particle class
    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 2 + 1;
        this.speedX = (Math.random() - 0.5) * 0.5;
        this.speedY = (Math.random() - 0.5) * 0.5;
        this.opacity = Math.random() * 0.5 + 0.2;
      }

      update() {
        this.x += this.speedX;
        this.y += this.speedY;

        // Wrap around edges
        if (this.x > canvas.width) this.x = 0;
        if (this.x < 0) this.x = canvas.width;
        if (this.y > canvas.height) this.y = 0;
        if (this.y < 0) this.y = canvas.height;
      }

      draw() {
        ctx.fillStyle = `rgba(0, 102, 204, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Create particles
    const createParticles = () => {
      particles = [];
      const particleCount = Math.floor((canvas.width * canvas.height) / 15000);
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    };
    createParticles();

    // Draw connections between nearby particles
    const connectParticles = () => {
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 150) {
            const opacity = (1 - distance / 150) * 0.2;
            ctx.strokeStyle = `rgba(0, 102, 204, ${opacity})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
    };

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach(particle => {
        particle.update();
        particle.draw();
      });

      connectParticles();

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    // Cleanup
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="landing-page">
      <canvas ref={canvasRef} className="particle-canvas" />

      <div className="landing-content">
        <div className="landing-hero fade-in">
          <div className="logo-container">
            <div className="logo-shield">
              <FaRoute className="logo-icon" />
            </div>
          </div>

          <h1 className="landing-title">
            Safer Routes<br />Anywhere, Anytime
          </h1>

          <p className="landing-subtitle">
            Navigate with confidence using real-time safety data and community reports
          </p>

          <div className="cta-buttons">
            <button
              className="btn btn-primary btn-lg cta-button"
              onClick={() => navigate('/route-planning')}
            >
              <FaRoute className="btn-icon" />
              Plan Your Route
            </button>

            <button
              className="btn btn-outline btn-lg cta-button"
              onClick={() => navigate('/report-incident')}
            >
              <FaExclamationTriangle className="btn-icon" />
              Report an Incident
            </button>
          </div>

          <div className="features-grid">
            <div></div>
            <div className="feature-item">
              <div className="feature-icon">🛡️</div>
              <h3>Safety First</h3>
              <p>Routes prioritized by safety scores</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🗺️</div>
              <h3>Smart Navigation</h3>
              <p>Turn-by-turn directions optimized for you</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">👥</div>
              <h3>Community Powered</h3>
              <p>Real-time incident reports from users</p>
            </div>
            <div></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
