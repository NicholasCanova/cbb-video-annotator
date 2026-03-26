import { forwardRef, useState, useEffect } from 'react';
import { Box, Text } from '@mantine/core';
import { useVideoStore } from '../../stores/useVideoStore';
import { VideoOverlay } from './VideoOverlay';
import { EventBadges } from './EventBadges';

interface VideoPlayerProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
}

export const VideoPlayer = forwardRef<HTMLDivElement, VideoPlayerProps>(
  function VideoPlayer({ videoRef }, ref) {
    const videoSrc = useVideoStore((s) => s.videoSrc);
    const fileName = useVideoStore((s) => s.fileName);
    const [error, setError] = useState<string | null>(null);

    // Reset error when source changes
    useEffect(() => {
      setError(null);
    }, [videoSrc]);

    const handleError = () => {
      const v = videoRef.current;
      if (v?.error) {
        const ext = fileName?.split('.').pop()?.toLowerCase() ?? '';
        if (['mov', 'mkv', 'avi', 'wmv'].includes(ext)) {
          setError(
            `Cannot play .${ext} files in the browser. Please convert to MP4 (H.264) first.`
          );
        } else {
          setError(`Video format not supported by this browser (error code ${v.error.code}).`);
        }
      }
    };

    return (
      <Box
        ref={ref}
        pos="relative"
        style={{
          flex: 1,
          minHeight: 0,
          background: '#000',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        {videoSrc ? (
          <>
            <video
              ref={videoRef}
              src={videoSrc}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                width: '100%',
                height: '100%',
                objectFit: 'contain',
              }}
              preload="auto"
              onError={handleError}
            />
            {error ? (
              <Box
                pos="absolute"
                top="50%"
                left="50%"
                style={{ transform: 'translate(-50%, -50%)', textAlign: 'center', maxWidth: 400 }}
              >
                <Text c="red" fw={600} size="lg">
                  {error}
                </Text>
                <Text c="dimmed" size="sm" mt="xs">
                  Tip: Use ffmpeg to convert: ffmpeg -i input.mov -c:v libx264 output.mp4
                </Text>
              </Box>
            ) : (
              <>
                <VideoOverlay />
                <EventBadges />
              </>
            )}
          </>
        ) : (
          <Box c="dimmed" fz="lg">
            Open a video file to begin
          </Box>
        )}
      </Box>
    );
  }
);
