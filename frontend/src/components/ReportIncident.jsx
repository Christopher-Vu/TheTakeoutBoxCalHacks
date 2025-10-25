import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FaArrowLeft,
  FaUpload,
  FaMapMarkerAlt,
  FaCalendarAlt,
  FaFilter,
  FaTimes
} from 'react-icons/fa';
import { mockIncidents, getTimeAgo, incidentTypeLabels, incidentTypeColors } from '../utils/mockData';
import './ReportIncident.css';

const ReportIncident = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    type: 'theft',
    description: '',
    location: '',
    dateTime: '',
    image: null
  });
  const [imagePreview, setImagePreview] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [showSuccess, setShowSuccess] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleImageUpload = (file) => {
    if (file && file.type.startsWith('image/')) {
      setFormData(prev => ({ ...prev, image: file }));
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleImageUpload(e.target.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock submission
    console.log('Submitting incident report:', formData);
    setShowSuccess(true);
    setTimeout(() => {
      setShowSuccess(false);
      // Reset form
      setFormData({
        type: 'theft',
        description: '',
        location: '',
        dateTime: '',
        image: null
      });
      setImagePreview(null);
    }, 2000);
  };

  const filteredIncidents = filterType === 'all'
    ? mockIncidents
    : mockIncidents.filter(incident => incident.type === filterType);

  return (
    <div className="report-incident-page">
      <div className="report-main-content">
        <div className="report-header">
          <button className="btn-back" onClick={() => navigate('/')}>
            <FaArrowLeft /> Back to Home
          </button>
          <h1>Report an Incident</h1>
          <p className="report-subtitle">Help keep your community safe by reporting incidents</p>
        </div>

        <form className="incident-form card" onSubmit={handleSubmit}>
          <div className="form-section">
            <label className="label">Incident Type</label>
            <select
              name="type"
              value={formData.type}
              onChange={handleInputChange}
              className="select"
              required
            >
              <option value="theft">Theft</option>
              <option value="assault">Assault</option>
              <option value="harassment">Harassment</option>
              <option value="vandalism">Vandalism</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="form-section">
            <label className="label">
              <FaMapMarkerAlt /> Location
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleInputChange}
              className="input"
              placeholder="Enter location or address"
              required
            />
          </div>

          <div className="form-section">
            <label className="label">
              <FaCalendarAlt /> Date & Time
            </label>
            <input
              type="datetime-local"
              name="dateTime"
              value={formData.dateTime}
              onChange={handleInputChange}
              className="input"
              required
            />
          </div>

          <div className="form-section">
            <label className="label">Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              className="textarea"
              placeholder="Describe what happened in detail..."
              required
            />
          </div>

          <div className="form-section">
            <label className="label">
              <FaUpload /> Upload Image (Optional)
            </label>
            <div
              className={`upload-area ${dragActive ? 'drag-active' : ''} ${imagePreview ? 'has-image' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {imagePreview ? (
                <div className="image-preview">
                  <img src={imagePreview} alt="Preview" />
                  <button
                    type="button"
                    className="remove-image-btn"
                    onClick={() => {
                      setImagePreview(null);
                      setFormData(prev => ({ ...prev, image: null }));
                    }}
                  >
                    <FaTimes /> Remove
                  </button>
                </div>
              ) : (
                <>
                  <FaUpload className="upload-icon" />
                  <p>Drag and drop an image here</p>
                  <p className="upload-or">or</p>
                  <label className="upload-label">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileInput}
                      style={{ display: 'none' }}
                    />
                    <span className="btn btn-outline">Browse Files</span>
                  </label>
                </>
              )}
            </div>
          </div>

          <button type="submit" className="btn btn-success btn-lg submit-btn">
            Submit Report
          </button>

          {showSuccess && (
            <div className="success-message scale-in">
              ✓ Report submitted successfully! Thank you for helping keep the community safe.
            </div>
          )}
        </form>
      </div>

      <aside className="incidents-sidebar">
        <div className="sidebar-header">
          <h2>Recent Reports</h2>
          <div className="filter-section">
            <FaFilter />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Types</option>
              <option value="theft">Theft</option>
              <option value="assault">Assault</option>
              <option value="harassment">Harassment</option>
              <option value="vandalism">Vandalism</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <div className="incidents-list">
          {filteredIncidents.map((incident, index) => (
            <div
              key={incident.id}
              className="incident-card fade-in"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="incident-header">
                <span className={`badge badge-${incidentTypeColors[incident.type]}`}>
                  {incidentTypeLabels[incident.type]}
                </span>
                <span className="incident-time">{getTimeAgo(incident.dateTime)}</span>
              </div>
              <div className="incident-location">
                <FaMapMarkerAlt />
                {incident.location}
              </div>
              <p className="incident-description">{incident.description}</p>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
};

export default ReportIncident;
