import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FaArrowLeft,
  FaUpload,
  FaMapMarkerAlt,
  FaCalendarAlt,
  FaFilter,
  FaTimes,
  FaRobot,
  FaCheck,
  FaTimes as FaX
} from 'react-icons/fa';
import { mockIncidents, getTimeAgo, incidentTypeLabels, incidentTypeColors } from '../utils/mockData';
import AddressAutocomplete from './AddressAutocomplete';
import './ReportIncident.css';

const ReportIncident = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    type: '',
    description: '',
    location: '',
    locationCoords: null, // { lat, lng, address }
    dateTime: '',
    image: null
  });
  const [imagePreview, setImagePreview] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [showSuccess, setShowSuccess] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [showAiModal, setShowAiModal] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState(null);

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

  const handleLocationSelect = (locationData) => {
    setFormData(prev => ({
      ...prev,
      location: locationData.name,
      locationCoords: {
        lat: locationData.lat,
        lng: locationData.lng,
        address: locationData.name
      }
    }));
  };

  const analyzeImage = async () => {
    if (!formData.image) return;
    
    setIsAnalyzing(true);
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('image', formData.image);
      
      const response = await fetch('http://localhost:8000/api/incident/analyze-image', {
        method: 'POST',
        body: formDataToSend
      });
      
      if (!response.ok) {
        throw new Error('Analysis failed');
      }
      
      const analysis = await response.json();
      setAiAnalysis(analysis);
      setShowAiModal(true);
    } catch (error) {
      console.error('Image analysis error:', error);
      setSubmissionStatus({ type: 'error', message: 'Failed to analyze image' });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const acceptAiSuggestion = () => {
    if (aiAnalysis) {
      const categoryMapping = {
        'THEFT': 'theft',
        'VANDALISM': 'vandalism',
        'ASSAULT': 'assault',
        'BURGLARY': 'burglary',
        'OTHER': 'other'
      };
      
      const frontendCategory = categoryMapping[aiAnalysis.suggested_category] || 'other';
      
      setFormData(prev => ({
        ...prev,
        type: prev.type || frontendCategory,
        description: prev.description || aiAnalysis.description
      }));
    }
    setShowAiModal(false);
  };

  const rejectAiSuggestion = () => {
    setShowAiModal(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.locationCoords) {
      setSubmissionStatus({ type: 'error', message: 'Please select a location from the dropdown' });
      return;
    }
    
    if (!formData.dateTime) {
      setSubmissionStatus({ type: 'error', message: 'Please enter the incident date and time' });
      return;
    }
    
    setSubmissionStatus({ type: 'loading', message: 'Submitting incident...' });
    
    try {
      const submitData = new FormData();
      submitData.append('lat', formData.locationCoords.lat);
      submitData.append('lng', formData.locationCoords.lng);
      submitData.append('address', formData.locationCoords.address);
      submitData.append('category', formData.type || 'other');
      submitData.append('datetime_str', formData.dateTime);
      submitData.append('description', formData.description);
      
      const response = await fetch('http://localhost:8000/api/incident/submit', {
        method: 'POST',
        body: submitData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Submission failed');
      }
      
      const result = await response.json();
      setSubmissionStatus({ type: 'success', message: 'Incident submitted successfully!', data: result.incident });
      
      setTimeout(() => {
        setFormData({
          type: '',
          description: '',
          location: '',
          locationCoords: null,
          dateTime: '',
          image: null
        });
        setImagePreview(null);
        setSubmissionStatus(null);
      }, 3000);
      
    } catch (error) {
      console.error('Submission error:', error);
      setSubmissionStatus({ type: 'error', message: error.message });
    }
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
            <label className="label">Incident Type (Optional)</label>
            <select
              name="type"
              value={formData.type}
              onChange={handleInputChange}
              className="select"
            >
              <option value="">Select incident type...</option>
              <option value="theft">Theft</option>
              <option value="assault">Assault</option>
              <option value="harassment">Harassment</option>
              <option value="vandalism">Vandalism</option>
              <option value="burglary">Burglary</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="form-section">
            <label className="label">
              <FaMapMarkerAlt /> Location
            </label>
            <AddressAutocomplete
              value={formData.location}
              onChange={setFormData}
              onSelect={handleLocationSelect}
              placeholder="Enter location or address"
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
            <label className="label">Description (Optional)</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              className="textarea"
              placeholder="Describe what happened in detail..."
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
                  <div className="image-actions">
                    <button
                      type="button"
                      className="btn btn-primary analyze-btn"
                      onClick={analyzeImage}
                      disabled={isAnalyzing}
                    >
                      <FaRobot /> {isAnalyzing ? 'Analyzing...' : 'Analyze Image'}
                    </button>
                    <button
                      type="button"
                      className="remove-image-btn"
                      onClick={() => {
                        setImagePreview(null);
                        setFormData(prev => ({ ...prev, image: null }));
                        setAiAnalysis(null);
                      }}
                    >
                      <FaTimes /> Remove
                    </button>
                  </div>
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

          {submissionStatus && (
            <div className={`status-message ${submissionStatus.type}`}>
              {submissionStatus.type === 'loading' && <div className="spinner"></div>}
              {submissionStatus.message}
              {submissionStatus.data && (
                <div className="incident-details">
                  <p><strong>Incident ID:</strong> {submissionStatus.data.id}</p>
                  <p><strong>Type:</strong> {submissionStatus.data.crime_type}</p>
                  <p><strong>Location:</strong> {submissionStatus.data.address}</p>
                </div>
              )}
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

      {/* AI Analysis Modal */}
      {showAiModal && aiAnalysis && (
        <div className="modal-overlay">
          <div className="modal-content ai-analysis-modal">
            <div className="modal-header">
              <h3><FaRobot /> AI Analysis Results</h3>
              <button className="close-btn" onClick={rejectAiSuggestion}>
                <FaX />
              </button>
            </div>
            <div className="modal-body">
              <div className="analysis-result">
                <div className="suggestion">
                  <h4>Suggested Category:</h4>
                  <span className="suggested-category">
                    {aiAnalysis.suggested_category}
                  </span>
                  <span className={`confidence ${aiAnalysis.confidence > 0.7 ? 'high' : aiAnalysis.confidence > 0.5 ? 'medium' : 'low'}`}>
                    (Confidence: {Math.round(aiAnalysis.confidence * 100)}%)
                  </span>
                </div>
                <div className="description">
                  <h4>Description:</h4>
                  <p>{aiAnalysis.description}</p>
                </div>
                {aiAnalysis.keywords && aiAnalysis.keywords.length > 0 && (
                  <div className="keywords">
                    <h4>Keywords:</h4>
                    <div className="keyword-tags">
                      {aiAnalysis.keywords.map((keyword, index) => (
                        <span key={index} className="keyword-tag">{keyword}</span>
                      ))}
                    </div>
                  </div>
                )}
                {aiAnalysis.reasoning && (
                  <div className="reasoning">
                    <h4>Reasoning:</h4>
                    <p>{aiAnalysis.reasoning}</p>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={rejectAiSuggestion}>
                <FaX /> Reject
              </button>
              <button className="btn btn-primary" onClick={acceptAiSuggestion}>
                <FaCheck /> Accept Suggestion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportIncident;
