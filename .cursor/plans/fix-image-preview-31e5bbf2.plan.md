<!-- 31e5bbf2-6066-4884-9211-d82eceb853a1 c30706cc-88a6-4063-b15f-7c6a46a2e16e -->
# Groq Image Analysis Integration Plan

## Overview

Add Groq AI-powered image analysis to the Report Incident page, allowing users to upload crime scene photos that auto-populate crime type and description. Integrate OpenStreetMap address autocomplete and save reports to a test dataset.

## Backend Changes

### 1. Install Groq Package

Add `groq` to `backend/requirements.txt` and install it:

```
groq==0.4.1
```

### 2. Create Backend Endpoint for Image Analysis

Add new endpoint `POST /api/incident/analyze-image` in `backend/main.py`:

- Accept multipart form data with image file
- Initialize Groq client with API key from `.env` file
- Use `llama-3.2-90b-vision-preview` model
- Return JSON with:
  - `suggested_category`: Crime type (THEFT, ASSAULT, VANDALISM, etc.)
  - `confidence`: Float 0.0-1.0
  - `description`: AI-generated description
  - `reasoning`: Why AI chose this category

### 3. Create Endpoint to Save User Reports

Add new endpoint `POST /api/incident/submit` in `backend/main.py`:

- Accept form data: lat, lng, address, category, datetime, description (optional), image (optional)
- Generate unique incident ID
- Save to `data/test_incidents.json` with structure:
```json
{
  "incidents": [
    {
      "id": "user_001",
      "crime_type": "THEFT",
      "lat": 37.8719,
      "lng": -122.2585,
      "address": "Telegraph Ave, Berkeley",
      "occurred_datetime": "2024-10-26T14:30:00",
      "description": "...",
      "source": "user_reported",
      "confidence": 0.85
    }
  ]
}
```


### 4. Setup Environment Variables

Create `backend/.env` file to store Groq API key:

```
GROQ_API_KEY=your_key_here
```

## Frontend Changes

### 1. Update ReportIncident Component (`frontend/src/components/ReportIncident.jsx`)

**Replace location input with AddressAutocomplete:**

- Import `AddressAutocomplete` component
- Replace text input with `<AddressAutocomplete />` 
- Store selected address with lat/lng coordinates
- Update form state to include `locationCoords: { lat, lng, address }`

**Make crime type and description optional:**

- Remove `required` attribute from type select
- Remove `required` attribute from description textarea
- Keep location and datetime as required

**Add AI Analysis Flow:**

- Add "Analyze Image" button (appears when image is uploaded)
- Add state for AI analysis results and loading state
- Create `analyzeImage()` function:
  - Send image to `/api/incident/analyze-image`
  - Show loading spinner during analysis
  - Display results in modal with suggested category, confidence, description
- Add modal UI showing:
  - Suggested crime type
  - Confidence score
  - AI-generated description
  - "Accept" button (auto-fills form fields)
  - "Reject" button (dismisses modal)

**Update form submission:**

- Send data to `/api/incident/submit` endpoint
- Include lat/lng from address autocomplete
- Handle success/error responses
- Show confirmation message

### 2. Update Styles (`frontend/src/components/ReportIncident.css`)

- Add styles for "Analyze Image" button
- Add modal styles for AI suggestions display
- Add loading spinner styles
- Add confidence indicator styles (color-coded: green >0.7, yellow 0.5-0.7, red <0.5)

## File Structure

```
backend/
  .env (new) - Store GROQ_API_KEY
  main.py (modify) - Add /api/incident/analyze-image and /api/incident/submit
  requirements.txt (modify) - Add groq package

data/
  test_incidents.json (new) - Store user-reported incidents

frontend/src/components/
  ReportIncident.jsx (modify) - Add address autocomplete, AI analysis, submission
  ReportIncident.css (modify) - Add new styles
```

## Implementation Flow

1. User types address → OpenStreetMap dropdown appears → Select stores lat/lng
2. User uploads image → "Analyze Image" button appears
3. Click "Analyze Image" → Send to Groq API → Show modal with results
4. User accepts/rejects AI suggestions
5. If accepted, auto-fill crime type and description (only if empty)
6. User submits form → Save to `data/test_incidents.json`
7. Show success message and reset form

## Key Technical Details

- Use `python-dotenv` to load GROQ_API_KEY from `.env`
- Convert image to base64 for Groq API
- AddressAutocomplete already uses OpenStreetMap Nominatim API
- Form validation: require location (with coords) and datetime
- AI suggestions only fill empty fields (don't overwrite user input)