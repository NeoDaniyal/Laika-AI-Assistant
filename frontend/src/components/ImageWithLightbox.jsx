import React, { useState, useCallback } from 'react';
import { Controlled as ControlledZoom } from 'react-medium-image-zoom';
import 'react-medium-image-zoom/dist/styles.css';
import { FiDownload } from 'react-icons/fi';
import './ImageWithLightbox.css';
export const ImageWithLightbox = ({src, alt}) =>{
    const [isZoomed, setIsZoomed] = useState(false)

    const handleZoomChange = useCallback((shouldZoom) => {
        setIsZoomed(shouldZoom)
    }, []);

    const handleDownload = async (e) => {
        e.stopPropagation();

        try {
            const response = await fetch(src)
            const blob = await response.blob()
            const blobUrl = window.URL.createObjectURL(blob)

            const filename = src.split('/').pop() || 'downloaded_image.png'

            const link = document.createElement('a')
            link.click()

            document.body.removeChild(link)
            window.URL.revokeObjectURL(blobUrl)
        } catch (error) {
            console.error('Download failed', error)
            alert('Failed to download image. Is the backend serving the static file?')
        }
    }

    const OverlayControls = ()=>(
        <div className="lighbox-overlay-controls">
            <button className="lightbox-download-btn" onClick={handleDownload} title="Download Image">
                <FiDownload/>
                <span>Download</span>
            </button>
        </div>
    )
    return(
        <div className="image-with-lightbox">
            <ControlledZoom
            isZoomed={isZoomed}
            onZoomChange={handleZoomChange}
            OverlayComponent={OverlayControls}
            >
                <img src={src} alt={alt || 'Generated output'} />
            </ControlledZoom>

            {!isZoomed && (
                <div className="zoom-cue">
                    Click to Zoom
                </div>
            )}
        </div>
    )
}

