// static/js/horse-racing-events.js
import { getCSRFToken } from './utils.js';

export async function fetchEvents() {
    console.log('Fetching race data from: /horse-racing/cards-json/');
    try {
        const response = await fetch('/horse-racing/cards-json/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
        });
        console.log(`Response status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Fetched ${data.length} horse racing events`, data);
        return data;
    } catch (error) {
        console.error('Error fetching race data:', error);
        return [];
    }
}

export function formatEventList(events, sport, category, isCentral = false) {
    // Not used, as renderHorseRacingEvents handles rendering
    return '';
}