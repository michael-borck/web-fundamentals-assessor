import os
import argparse
import re
import json
import csv
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageStat
import cv2
import glob
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd


class ResponsiveDesignAnalyzer:
    def __init__(self, output_dir="responsive_analysis"):
        """
        Initialize the responsive design analyzer.

        Args:
            output_dir: Directory to save analysis reports
        """
        self.output_dir = output_dir

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Define responsive design patterns to look for
        self.media_query_patterns = {
            'max_width': r'@media\s+\(\s*max-width\s*:\s*(\d+)px\s*\)',
            'min_width': r'@media\s+\(\s*min-width\s*:\s*(\d+)px\s*\)',
            'orientation': r'@media\s+\(\s*orientation\s*:\s*(portrait|landscape)\s*\)',
            'device_type': r'@media\s+\(\s*only\s+screen\s+and\s+\(\s*max-device-width\s*:\s*(\d+)px\s*\)\s*\)',
        }

        # Define responsive CSS features (non-media query)
        self.responsive_css_features = {
            'relative_units': {
                'percentage': r':\s*(-?\d+\.?\d*)%',
                'em': r':\s*(-?\d+\.?\d*)em',
                'rem': r':\s*(-?\d+\.?\d*)rem',
                'vh': r':\s*(-?\d+\.?\d*)vh',
                'vw': r':\s*(-?\d+\.?\d*)vw',
            },
            'responsive_layouts': {
                'flexbox': r'display\s*:\s*flex',
                'grid': r'display\s*:\s*grid',
                'grid_template': r'grid-template-(columns|rows|areas)',
                'flex_wrap': r'flex-wrap\s*:\s*wrap',
                'flex_direction': r'flex-direction\s*:',
            },
            'responsive_elements': {
                'max_width': r'max-width\s*:\s*\d+',
                'min_width': r'min-width\s*:\s*\d+',
                'calc_function': r'calc\s*\(',
                'object_fit': r'object-fit\s*:',
            }
        }

        # Define responsive HTML meta tags and attributes
        self.responsive_html_patterns = {
            'viewport_meta': r'<meta\s+name=["\']viewport["\'][^>]*content=["\'][^"\']*width=device-width[^"\']*["\']',
            'srcset_attribute': r'srcset=["\'][^"\']+["\']',
            'sizes_attribute': r'sizes=["\'][^"\']+["\']',
            'picture_element': r'<picture\b',
            'source_media': r'<source[^>]*media=["\'][^"\']+["\']',
        }

        # Common device breakpoints
        self.common_breakpoints = [
            480,  # Mobile
            768,  # Tablet
            992,  # Desktop
            1200, # Large desktop
        ]

        # Define weights for different aspects of responsive design
        self.weights = {
            'screenshot_similarity': 0.40,   # Screenshot comparison weight
            'css_responsive_features': 0.35, # CSS features weight
            'html_responsive_features': 0.25, # HTML features weight
        }

    def analyze_css_file(self, file_path):
        """
        Analyze a CSS file for responsive design patterns.

        Args:
            file_path: Path to the CSS file

        Returns:
            Dictionary with CSS analysis results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()

            # Initialize results
            media_queries = {}
            features = {category: {} for category in self.responsive_css_features}

            # Extract all media queries
            for query_type, pattern in self.media_query_patterns.items():
                matches = re.findall(pattern, css_content)
                media_queries[query_type] = matches

            # Calculate number of unique breakpoints in media queries
            breakpoints = set()
            for query_type in ['max_width', 'min_width']:
                if query_type in media_queries:
                    for value in media_queries[query_type]:
                        try:
                            breakpoints.add(int(value))
                        except ValueError:
                            pass

            # Check for common breakpoints
            common_breakpoints_used = sum(1 for bp in breakpoints if any(abs(bp - common) <= 20 for common in self.common_breakpoints))

            # Extract responsive CSS features
            for category, patterns in self.responsive_css_features.items():
                for feature, pattern in patterns.items():
                    matches = re.findall(pattern, css_content)
                    features[category][feature] = len(matches)

            # Calculate statistics
            total_media_queries = sum(len(matches) for matches in media_queries.values())

            # Relative units usage
            relative_units = sum(features['relative_units'].values())

            # Layout features
            layout_features = sum(features['responsive_layouts'].values())

            # Element features
            element_features = sum(features['responsive_elements'].values())

            # Calculate an overall responsive CSS score (0-10)
            css_score = self._calculate_css_score(
                total_media_queries,
                len(breakpoints),
                common_breakpoints_used,
                relative_units,
                layout_features,
                element_features
            )

            return {
                'file_path': file_path,
                'media_queries': media_queries,
                'breakpoints': sorted(list(breakpoints)),
                'common_breakpoints_used': common_breakpoints_used,
                'features': features,
                'statistics': {
                    'total_media_queries': total_media_queries,
                    'unique_breakpoints': len(breakpoints),
                    'relative_units': relative_units,
                    'layout_features': layout_features,
                    'element_features': element_features,
                },
                'css_score': css_score
            }

        except Exception as e:
            print(f"Error analyzing CSS file {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e)
            }

    def analyze_html_file(self, file_path):
        """
        Analyze an HTML file for responsive design patterns.

        Args:
            file_path: Path to the HTML file

        Returns:
            Dictionary with HTML analysis results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Initialize results
            responsive_features = {}

            # Check for responsive HTML patterns
            for feature, pattern in self.responsive_html_patterns.items():
                matches = re.findall(pattern, html_content)
                responsive_features[feature] = len(matches)

            # Check if viewport meta tag is present
            has_viewport_meta = responsive_features['viewport_meta'] > 0

            # Check for responsive image features
            responsive_images = (
                responsive_features['srcset_attribute'] +
                responsive_features['sizes_attribute'] +
                responsive_features['picture_element'] +
                responsive_features['source_media']
            )

            # Calculate an overall responsive HTML score (0-10)
            html_score = self._calculate_html_score(
                has_viewport_meta,
                responsive_images
            )

            return {
                'file_path': file_path,
                'responsive_features': responsive_features,
                'has_viewport_meta': has_viewport_meta,
                'responsive_images': responsive_images,
                'html_score': html_score
            }

        except Exception as e:
            print(f"Error analyzing HTML file {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e)
            }

    def _calculate_css_score(self, total_media_queries, unique_breakpoints, common_breakpoints_used,
                            relative_units, layout_features, element_features):
        """
        Calculate a responsive CSS score (0-10).
        """
        score = 0

        # Media queries (0-4 points)
        if total_media_queries >= 10:
            score += 4
        elif total_media_queries >= 6:
            score += 3
        elif total_media_queries >= 3:
            score += 2
        elif total_media_queries >= 1:
            score += 1

        # Breakpoints (0-2 points)
        if unique_breakpoints >= 4:
            score += 2
        elif unique_breakpoints >= 2:
            score += 1

        # Common breakpoints (0-1 point)
        if common_breakpoints_used >= 2:
            score += 1

        # Relative units (0-1 point)
        if relative_units >= 15:
            score += 1
        elif relative_units >= 8:
            score += 0.5

        # Layout features (0-1.5 points)
        if layout_features >= 8:
            score += 1.5
        elif layout_features >= 4:
            score += 1
        elif layout_features >= 1:
            score += 0.5

        # Element features (0-0.5 point)
        if element_features >= 5:
            score += 0.5
        elif element_features >= 2:
            score += 0.25

        return min(10, score)

    def _calculate_html_score(self, has_viewport_meta, responsive_images):
        """
        Calculate a responsive HTML score (0-10).
        """
        score = 0

        # Viewport meta tag (0-5 points)
        if has_viewport_meta:
            score += 5

        # Responsive images (0-5 points)
        if responsive_images >= 10:
            score += 5
        elif responsive_images >= 5:
            score += 3
        elif responsive_images >= 1:
            score += 1

        return min(10, score)

    def compare_screenshots(self, desktop_path, mobile_path):
        """
        Compare desktop and mobile screenshots to assess responsiveness.

        Args:
            desktop_path: Path to desktop screenshot
            mobile_path: Path to mobile screenshot

        Returns:
            Dictionary with comparison results
        """
        try:
            # Load images
            desktop_img = Image.open(desktop_path)
            mobile_img = Image.open(mobile_path)

            # Extract file names
            desktop_name = os.path.basename(desktop_path)
            mobile_name = os.path.basename(mobile_path)

            # Calculate scaling factor based on width ratio
            desktop_width, desktop_height = desktop_img.size
            mobile_width, mobile_height = mobile_img.size
            width_ratio = desktop_width / mobile_width

            # Convert to OpenCV format for processing
            desktop_cv = cv2.cvtColor(np.array(desktop_img), cv2.COLOR_RGB2BGR)
            mobile_cv = cv2.cvtColor(np.array(mobile_img), cv2.COLOR_RGB2BGR)

            # Calculate histograms
            desktop_hist = cv2.calcHist([desktop_cv], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            mobile_hist = cv2.calcHist([mobile_cv], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

            # Normalize histograms
            cv2.normalize(desktop_hist, desktop_hist)
            cv2.normalize(mobile_hist, mobile_hist)

            # Calculate histogram similarity
            hist_similarity = cv2.compareHist(desktop_hist, mobile_hist, cv2.HISTCMP_CORREL)

            # Resize mobile image to desktop width for direct comparison
            mobile_resized = cv2.resize(mobile_cv, (desktop_width, int(mobile_height * desktop_width / mobile_width)))

            # Create a visual comparison and heatmap
            comparison_path = os.path.join(self.output_dir, f"compare_{os.path.splitext(desktop_name)[0]}.png")
            heatmap_path = os.path.join(self.output_dir, f"heatmap_{os.path.splitext(desktop_name)[0]}.png")

            # Create visualization only if mobile_resized height is not too large compared to desktop
            height_diff = abs(mobile_resized.shape[0] - desktop_cv.shape[0])
            if height_diff <= desktop_cv.shape[0] * 2:  # Limit to reasonable size difference
                # Create visualization for comparison
                self._create_comparison_image(desktop_cv, mobile_resized, comparison_path)

                # Create heatmap for differences
                self._create_difference_heatmap(desktop_cv, mobile_resized, heatmap_path)
            else:
                comparison_path = None
                heatmap_path = None
                print(f"Skipping visualization for {desktop_name} - height difference too large")

            # Calculate layout difference score (0-10)
            layout_score = self._calculate_layout_difference_score(desktop_cv, mobile_resized, width_ratio)

            return {
                'desktop_path': desktop_path,
                'mobile_path': mobile_path,
                'desktop_size': desktop_img.size,
                'mobile_size': mobile_img.size,
                'width_ratio': width_ratio,
                'hist_similarity': hist_similarity,
                'layout_score': layout_score,
                'comparison_path': comparison_path,
                'heatmap_path': heatmap_path
            }

        except Exception as e:
            print(f"Error comparing screenshots {desktop_path} and {mobile_path}: {e}")
            return {
                'desktop_path': desktop_path,
                'mobile_path': mobile_path,
                'error': str(e)
            }

    def _create_comparison_image(self, desktop_img, mobile_img, output_path):
        """
        Create a side-by-side comparison image of desktop and mobile views.
        """
        # Determine max height
        max_height = max(desktop_img.shape[0], mobile_img.shape[0])

        # Create blank canvases to match max height
        desktop_canvas = np.zeros((max_height, desktop_img.shape[1], 3), dtype=np.uint8)
        mobile_canvas = np.zeros((max_height, mobile_img.shape[1], 3), dtype=np.uint8)

        # Copy original images to canvases
        desktop_canvas[:desktop_img.shape[0], :desktop_img.shape[1]] = desktop_img
        mobile_canvas[:mobile_img.shape[0], :mobile_img.shape[1]] = mobile_img

        # Create side-by-side comparison with padding
        padding = np.zeros((max_height, 20, 3), dtype=np.uint8)
        comparison = np.hstack((desktop_canvas, padding, mobile_canvas))

        # Add labels
        cv2.putText(comparison, "Desktop", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(comparison, "Mobile", (desktop_canvas.shape[1] + 30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Save the comparison image
        cv2.imwrite(output_path, comparison)

    def _create_difference_heatmap(self, desktop_img, mobile_img, output_path):
        """
        Create a heatmap showing differences between desktop and mobile views.
        """
        # Ensure both images have the same height for comparison
        height = min(desktop_img.shape[0], mobile_img.shape[0])
        desktop_crop = desktop_img[:height, :, :]
        mobile_crop = mobile_img[:height, :, :]

        # Calculate absolute difference
        if desktop_crop.shape[1] != mobile_crop.shape[1]:
            # Resize mobile to match desktop width
            mobile_crop = cv2.resize(mobile_crop, (desktop_crop.shape[1], mobile_crop.shape[0]))

        diff = cv2.absdiff(desktop_crop, mobile_crop)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Create a normalized colormap for the heatmap
        plt.figure(figsize=(12, 8))
        plt.imshow(diff_gray, cmap='hot')
        plt.colorbar(label='Difference Intensity')
        plt.title('Desktop vs Mobile Difference Heatmap')
        plt.savefig(output_path)
        plt.close()

    def _calculate_layout_difference_score(self, desktop_img, mobile_img, width_ratio):
        """
        Calculate a score (0-10) representing the appropriate layout changes between desktop and mobile.

        Higher scores indicate better responsive adaptation.
        Lower scores indicate either no adaptation or poor adaptation.
        """
        # Initialize score
        score = 5  # Start at middle

        # Determine common height for comparison
        min_height = min(desktop_img.shape[0], mobile_img.shape[0])
        desktop_crop = desktop_img[:min_height, :, :]

        # Resize mobile to desktop width for direct comparison
        if mobile_img.shape[1] != desktop_img.shape[1]:
            mobile_resized = cv2.resize(mobile_img, (desktop_img.shape[1], int(mobile_img.shape[0] * desktop_img.shape[1] / mobile_img.shape[1])))
        else:
            mobile_resized = mobile_img

        mobile_crop = mobile_resized[:min_height, :, :]

        # Calculate difference image
        diff = cv2.absdiff(desktop_crop, mobile_crop)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        diff_mean = np.mean(diff_gray)

        # 1. Check for appropriate level of difference
        # Too little difference might mean no responsive behavior
        # Too much difference might mean broken layout
        if diff_mean < 10:  # Very little difference - probably not responsive
            score -= 3
        elif diff_mean > 80:  # Very high difference - might be problematic
            score -= 2
        elif 30 <= diff_mean <= 60:  # Good range for responsive changes
            score += 3

        # 2. Check width ratio - should be significant for responsive design
        if width_ratio > 2:  # Good responsive behavior typically has desktop ~2-3x wider than mobile
            score += 1
        elif width_ratio > 1.5:
            score += 0.5

        # 3. Check edge histograms to detect layout differences
        edges_desktop = cv2.Canny(desktop_crop, 100, 200)
        edges_mobile = cv2.Canny(mobile_crop, 100, 200)

        # Compare horizontal and vertical edge distributions
        hist_horiz_desktop = np.sum(edges_desktop, axis=0)
        hist_horiz_mobile = np.sum(edges_mobile, axis=0)
        hist_vert_desktop = np.sum(edges_desktop, axis=1)
        hist_vert_mobile = np.sum(edges_mobile, axis=1)

        # Normalize histograms
        if np.sum(hist_horiz_desktop) > 0:
            hist_horiz_desktop = hist_horiz_desktop / np.sum(hist_horiz_desktop)
        if np.sum(hist_horiz_mobile) > 0:
            hist_horiz_mobile = hist_horiz_mobile / np.sum(hist_horiz_mobile)
        if np.sum(hist_vert_desktop) > 0:
            hist_vert_desktop = hist_vert_desktop / np.sum(hist_vert_desktop)
        if np.sum(hist_vert_mobile) > 0:
            hist_vert_mobile = hist_vert_mobile / np.sum(hist_vert_mobile)

        # Calculate differences in edge distributions
        horiz_diff = np.sum(np.abs(hist_horiz_desktop - hist_horiz_mobile))
        vert_diff = np.sum(np.abs(hist_vert_desktop - hist_vert_mobile))

        # Significant horizontal difference but less vertical difference
        # suggests good responsive behavior (columns becoming rows)
        if horiz_diff > 0.5 and vert_diff < 0.3:
            score += 1

        # Ensure score is within bounds
        return max(0, min(10, score))

    def analyze_page(self, html_path, css_paths, desktop_screenshot, mobile_screenshot):
        """
        Analyze a page's responsiveness using HTML, CSS, and screenshots.

        Args:
            html_path: Path to the HTML file
            css_paths: List of paths to CSS files
            desktop_screenshot: Path to desktop screenshot
            mobile_screenshot: Path to mobile screenshot

        Returns:
            Dictionary with combined analysis results
        """
        # Analyze HTML
        html_result = self.analyze_html_file(html_path)

        # Analyze CSS files
        css_results = []
        combined_css_score = 0
        for css_path in css_paths:
            css_result = self.analyze_css_file(css_path)
            css_results.append(css_result)
            if 'css_score' in css_result:
                combined_css_score += css_result['css_score']

        # Average CSS score if there are multiple CSS files
        if css_results:
            combined_css_score /= len(css_results)

        # Compare screenshots
        screenshot_result = self.compare_screenshots(desktop_screenshot, mobile_screenshot)

        # Calculate overall responsiveness score
        html_score = html_result.get('html_score', 0)
        layout_score = screenshot_result.get('layout_score', 0)

        # Weighted average of scores
        overall_score = (
            self.weights['css_responsive_features'] * combined_css_score +
            self.weights['html_responsive_features'] * html_score +
            self.weights['screenshot_similarity'] * layout_score
        )

        return {
            'html_path': html_path,
            'css_paths': css_paths,
            'desktop_screenshot': desktop_screenshot,
            'mobile_screenshot': mobile_screenshot,
            'html_analysis': html_result,
            'css_analysis': css_results,
            'screenshot_analysis': screenshot_result,
            'scores': {
                'html_score': html_score,
                'css_score': combined_css_score,
                'layout_score': layout_score,
                'overall_score': overall_score
            }
        }

    def generate_report(self, results, output_file):
        """
        Generate a Markdown report of responsive design analysis results.

        Args:
            results: List of page analysis results
            output_file: Path to save the report
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Responsive Design Analysis Report\n\n")

            # Calculate overall stats
            pages_analyzed = len(results)
            # Prevent division by zero if no pages were analyzed
            overall_score = sum(r.get('scores', {}).get('overall_score', 0) for r in results) / max(1, pages_analyzed)

            # Write summary
            f.write(f"## Summary\n\n")
            f.write(f"- **Pages Analyzed:** {pages_analyzed}\n")
            f.write(f"- **Average Responsiveness Score:** {overall_score:.2f}/10\n\n")

            # Map to rubric performance level
            performance_level = ""
            rubric_points = 0

            if overall_score >= 8.5:
                performance_level = "Distinction (75-100%)"
                percentage = min(100, 75 + (overall_score - 8.5) * 25 / 1.5)
                rubric_points = 7 * percentage / 100
            elif overall_score >= 7:
                performance_level = "Credit (65-74%)"
                percentage = 65 + (overall_score - 7) * 9 / 1.5
                rubric_points = 7 * percentage / 100
            elif overall_score >= 5:
                performance_level = "Pass (50-64%)"
                percentage = 50 + (overall_score - 5) * 14 / 2
                rubric_points = 7 * percentage / 100
            else:
                performance_level = "Fail (0-49%)"
                percentage = overall_score * 49 / 5
                rubric_points = 7 * percentage / 100

            f.write(f"## Rubric Assessment\n\n")
            f.write(f"### Responsive Design (Mobile-First) (7%)\n\n")
            f.write(f"**Performance Level:** {performance_level}\n\n")
            f.write(f"**Score:** {rubric_points:.2f}/7 points ({percentage:.1f}%)\n\n")

            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Excellent responsiveness with optimised layouts for all screen sizes; thoughtful adaptations for different devices | 5.25-7 |\n")
            f.write("| Credit (65-74%) | Good responsiveness across devices; consistent user experience on most screen sizes | 4.55-5.24 |\n")
            f.write("| Pass (50-64%) | Basic responsiveness; layout adapts to different screen sizes with some issues | 3.5-4.54 |\n")
            f.write("| Fail (0-49%) | Poor responsiveness; significant layout issues on different screen sizes | 0-3.49 |\n\n")

            # Effective use of Flexbox/Grid assessment
            flexbox_grid_score = 0
            total_css_files = 0
            total_flexbox = 0
            total_grid = 0

            for result in results:
                for css_result in result.get('css_analysis', []):
                    total_css_files += 1
                    if 'features' in css_result and 'responsive_layouts' in css_result['features']:
                        layouts = css_result['features']['responsive_layouts']
                        total_flexbox += layouts.get('flexbox', 0) + layouts.get('flex_wrap', 0) + layouts.get('flex_direction', 0)
                        total_grid += layouts.get('grid', 0) + layouts.get('grid_template', 0)

            # Calculate flexbox/grid score
            if total_css_files > 0:
                avg_flexbox = total_flexbox / total_css_files
                avg_grid = total_grid / total_css_files

                if avg_flexbox >= 8 or avg_grid >= 5 or (avg_flexbox >= 5 and avg_grid >= 3):
                    flexbox_grid_level = "Distinction (75-100%)"
                    flexbox_percentage = min(100, 75 + (avg_flexbox + avg_grid) * 25 / 15)
                    flexbox_grid_score = 4 * flexbox_percentage / 100
                elif avg_flexbox >= 5 or avg_grid >= 3 or (avg_flexbox >= 3 and avg_grid >= 2):
                    flexbox_grid_level = "Credit (65-74%)"
                    flexbox_percentage = 65 + ((avg_flexbox + avg_grid) - 5) * 9 / 3
                    flexbox_grid_score = 4 * flexbox_percentage / 100
                elif avg_flexbox >= 2 or avg_grid >= 1:
                    flexbox_grid_level = "Pass (50-64%)"
                    flexbox_percentage = 50 + ((avg_flexbox + avg_grid) - 2) * 14 / 3
                    flexbox_grid_score = 4 * flexbox_percentage / 100
                else:
                    flexbox_grid_level = "Fail (0-49%)"
                    flexbox_percentage = min(49, (avg_flexbox + avg_grid) * 49 / 2)
                    flexbox_grid_score = 4 * flexbox_percentage / 100
            else:
                flexbox_grid_level = "Fail (0-49%)"
                flexbox_percentage = 0
                flexbox_grid_score = 0


            # Prevent division by zero if no pages were analyzed
            if pages_analyzed > 0:
                pages_with_viewport = sum(1 for r in results if r.get('html_analysis', {}).get('has_viewport_meta', False))
                f.write(f"### Total Design & Responsiveness Score (Excluding Color Scheme/Typography)\n\n")
                # Calculate combined total score for responsiveness section
                total_responsive_score = rubric_points + flexbox_grid_score
                total_responsive_percentage = (total_responsive_score / 11) * 100

                f.write(f"**Score:** {total_responsive_score:.2f}/11 points ({total_responsive_percentage:.1f}%)\n\n")

                # Page-by-page analysis
                f.write("## Page-by-Page Analysis\n\n")

                for result in results:
                    html_path = result.get('html_path', 'Unknown')
                    html_name = os.path.basename(html_path)
                    scores = result.get('scores', {})

                    f.write(f"### {html_name}\n\n")
                    f.write(f"**Overall Responsiveness Score:** {scores.get('overall_score', 0):.2f}/10\n\n")

                    # Include thumbnail comparisons if available
                    screenshot_analysis = result.get('screenshot_analysis', {})
                    comparison_path = screenshot_analysis.get('comparison_path')
                    heatmap_path = screenshot_analysis.get('heatmap_path')

                    if comparison_path and os.path.exists(comparison_path):
                        rel_comparison_path = os.path.relpath(comparison_path, os.path.dirname(output_file))
                        f.write(f"**Visual Comparison:**\n\n")
                        f.write(f"![Desktop vs Mobile]({rel_comparison_path})\n\n")

                    if heatmap_path and os.path.exists(heatmap_path):
                        rel_heatmap_path = os.path.relpath(heatmap_path, os.path.dirname(output_file))
                        f.write(f"**Difference Heatmap:**\n\n")
                        f.write(f"![Difference Heatmap]({rel_heatmap_path})\n\n")

                    # Screenshot metrics
                    f.write("**Screenshot Analysis:**\n\n")
                    f.write(f"- Layout Adaptation Score: {scores.get('layout_score', 0):.2f}/10\n")
                    f.write(f"- Desktop-to-Mobile Width Ratio: {screenshot_analysis.get('width_ratio', 0):.2f}\n")
                    f.write(f"- Histogram Similarity: {screenshot_analysis.get('hist_similarity', 0):.2f}\n\n")

                    # HTML responsiveness
                    html_analysis = result.get('html_analysis', {})
                    f.write("**HTML Responsiveness Features:**\n\n")
                    f.write(f"- Viewport Meta Tag: {'Present' if html_analysis.get('has_viewport_meta', False) else 'Missing'}\n")

                    if 'responsive_features' in html_analysis:
                        features = html_analysis['responsive_features']
                        f.write(f"- Responsive Image Features: {html_analysis.get('responsive_images', 0)}\n")
                        f.write(f"  - srcset Attributes: {features.get('srcset_attribute', 0)}\n")
                        f.write(f"  - sizes Attributes: {features.get('sizes_attribute', 0)}\n")
                        f.write(f"  - picture Elements: {features.get('picture_element', 0)}\n")
                        f.write(f"  - source media Queries: {features.get('source_media', 0)}\n")
                    f.write(f"- HTML Score: {scores.get('html_score', 0):.2f}/10\n\n")

                    # CSS responsiveness
                    f.write("**CSS Responsiveness Features:**\n\n")

                    css_analysis = result.get('css_analysis', [])
                    if css_analysis:
                        # Combine breakpoints from all CSS files
                        all_breakpoints = set()
                        media_query_count = 0
                        flex_count = 0
                        grid_count = 0
                        relative_units = 0

                        for css_result in css_analysis:
                            if 'breakpoints' in css_result:
                                all_breakpoints.update(css_result['breakpoints'])

                            if 'statistics' in css_result:
                                stats = css_result['statistics']
                                media_query_count += stats.get('total_media_queries', 0)
                                relative_units += stats.get('relative_units', 0)

                            if 'features' in css_result and 'responsive_layouts' in css_result['features']:
                                layouts = css_result['features']['responsive_layouts']
                                flex_count += layouts.get('flexbox', 0) + layouts.get('flex_wrap', 0) + layouts.get('flex_direction', 0)
                                grid_count += layouts.get('grid', 0) + layouts.get('grid_template', 0)

                        f.write(f"- Media Queries: {media_query_count}\n")
                        f.write(f"- Breakpoints: {sorted(all_breakpoints)}\n")
                        f.write(f"- Flexbox Features: {flex_count}\n")
                        f.write(f"- Grid Features: {grid_count}\n")
                        f.write(f"- Relative Units: {relative_units}\n")
                        f.write(f"- CSS Score: {scores.get('css_score', 0):.2f}/10\n\n")
                    else:
                        f.write("No CSS analysis available.\n\n")

                    # Recommendations for improvement
                    f.write("**Recommendations:**\n\n")

                    # Generate specific recommendations based on scores
                    recommendations = []

                    # HTML recommendations
                    if not html_analysis.get('has_viewport_meta', False):
                        recommendations.append("Add a viewport meta tag to enable proper mobile scaling")

                    if html_analysis.get('responsive_images', 0) < 2:
                        recommendations.append("Implement responsive image techniques (srcset, sizes, picture elements)")

                    # CSS recommendations
                    if media_query_count < 3:
                        recommendations.append("Add more media queries to adapt layout at different screen sizes")

                    if len(all_breakpoints) < 2:
                        recommendations.append("Define additional breakpoints for better device coverage")

                    if flex_count < 3 and grid_count < 2:
                        recommendations.append("Increase usage of Flexbox and/or Grid for more responsive layouts")

                    if relative_units < 10:
                        recommendations.append("Use more relative units (%, em, rem, vh, vw) instead of fixed pixels")

                    # Layout recommendations based on screenshot analysis
                    if scores.get('layout_score', 0) < 5:
                        recommendations.append("Improve layout adaptation between desktop and mobile versions")

                    if screenshot_analysis.get('hist_similarity', 0) < 0.7:
                        recommendations.append("Ensure visual consistency between desktop and mobile versions")

                    # Output recommendations
                    if recommendations:
                        for i, rec in enumerate(recommendations, 1):
                            f.write(f"{i}. {rec}\n")
                    else:
                        f.write("No specific recommendations - responsive design implementation is good.\n")

                    f.write("\n---\n\n")

                # Summary of findings and best practices
                f.write("## Summary of Findings\n\n")

                # Calculate high-level statistics
                # This was causing the ZeroDivisionError, already handled above
                # pages_with_viewport = sum(1 for r in results if r.get('html_analysis', {}).get('has_viewport_meta', False))
                avg_media_queries = sum(
                    css_result.get('statistics', {}).get('total_media_queries', 0)
                    for result in results
                    for css_result in result.get('css_analysis', [])
                ) / max(1, sum(len(result.get('css_analysis', [])) for result in results))

                unique_breakpoints = set()
                for result in results:
                    for css_result in result.get('css_analysis', []):
                        if 'breakpoints' in css_result:
                            unique_breakpoints.update(css_result['breakpoints'])

                f.write(f"- **Pages with viewport meta tag:** {pages_with_viewport}/{pages_analyzed} ({pages_with_viewport/pages_analyzed*100:.1f}%)\n")
                f.write(f"- **Average media queries per CSS file:** {avg_media_queries:.1f}\n")
                f.write(f"- **Unique breakpoints across site:** {sorted(unique_breakpoints)}\n\n")

                # Best practices
                f.write("### Responsive Design Best Practices\n\n")
                f.write("1. **Mobile-First Approach**: Start with mobile layout and progressively enhance for larger screens\n")
                f.write("2. **Flexible Grids**: Use relative units and fluid grid systems rather than fixed pixel dimensions\n")
                f.write("3. **Media Queries**: Implement breakpoints at standard device sizes (e.g., 480px, 768px, 992px, 1200px)\n")
                f.write("4. **Flexbox & Grid**: Leverage these CSS layout systems for adaptive content organization\n")
                f.write("5. **Responsive Images**: Use srcset, sizes, and picture elements to serve optimized images\n")
                f.write("6. **Touch-Friendly UI**: Ensure interactive elements are properly sized for touch devices\n")
                f.write("7. **Performance**: Optimize load times for mobile by minimizing resources and using progressive loading\n")
            else:
                f.write("No pages were analyzed, so detailed analysis and recommendations are not available.\n\n")


    def generate_csv_report(self, results, output_file):
        """
        Generate a CSV report of responsive design analysis results.

        Args:
            results: List of page analysis results
            output_file: Path to save the CSV report
        """
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'Page', 'Overall Score', 'HTML Score', 'CSS Score', 'Layout Score',
                'Viewport Meta', 'Media Queries', 'Breakpoints', 'Flexbox Features',
                'Grid Features', 'Relative Units', 'Responsive Images'
            ])

            # Write data for each page
            for result in results:
                html_path = result.get('html_path', 'Unknown')
                html_name = os.path.basename(html_path)
                scores = result.get('scores', {})
                html_analysis = result.get('html_analysis', {})

                # Calculate CSS statistics
                media_query_count = 0
                breakpoints = set()
                flex_count = 0
                grid_count = 0
                relative_units = 0

                for css_result in result.get('css_analysis', []):
                    if 'breakpoints' in css_result:
                        breakpoints.update(css_result['breakpoints'])

                    if 'statistics' in css_result:
                        stats = css_result['statistics']
                        media_query_count += stats.get('total_media_queries', 0)
                        relative_units += stats.get('relative_units', 0)

                    if 'features' in css_result and 'responsive_layouts' in css_result['features']:
                        layouts = css_result['features']['responsive_layouts']
                        flex_count += layouts.get('flexbox', 0) + layouts.get('flex_wrap', 0) + layouts.get('flex_direction', 0)
                        grid_count += layouts.get('grid', 0) + layouts.get('grid_template', 0)

                writer.writerow([
                    html_name,
                    f"{scores.get('overall_score', 0):.2f}",
                    f"{scores.get('html_score', 0):.2f}",
                    f"{scores.get('css_score', 0):.2f}",
                    f"{scores.get('layout_score', 0):.2f}",
                    'Yes' if html_analysis.get('has_viewport_meta', False) else 'No',
                    media_query_count,
                    len(breakpoints),
                    flex_count,
                    grid_count,
                    relative_units,
                    html_analysis.get('responsive_images', 0)
                ])

    def find_html_files(self, folder_path):
        """
        Find all HTML files in a folder recursively.

        Args:
            folder_path: Path to the folder to search

        Returns:
            List of HTML file paths
        """
        html_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, file))
        return html_files

    def find_css_files(self, folder_path):
        """
        Find all CSS files in a folder recursively.

        Args:
            folder_path: Path to the folder to search

        Returns:
            List of CSS file paths
        """
        css_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.css'):
                    css_files.append(os.path.join(root, file))
        return css_files

    def find_linked_css_files(self, html_path, base_folder):
        """
        Find CSS files linked from an HTML file.

        Args:
            html_path: Path to the HTML file
            base_folder: Base folder to resolve relative paths

        Returns:
            List of paths to linked CSS files
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract CSS links
            css_links = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\']', html_content)

            # Resolve paths
            css_paths = []
            for link in css_links:
                if link.startswith('http://') or link.startswith('https://'):
                    # Skip external CSS
                    continue

                # Remove URL parameters if present
                link = link.split('?')[0]

                # Handle relative paths
                if link.startswith('/'):
                    # Absolute path relative to base folder
                    css_path = os.path.join(base_folder, link.lstrip('/'))
                else:
                    # Relative to HTML file
                    html_dir = os.path.dirname(html_path)
                    css_path = os.path.normpath(os.path.join(html_dir, link))

                if os.path.exists(css_path) and css_path.endswith('.css'):
                    css_paths.append(css_path)

            return css_paths

        except Exception as e:
            print(f"Error finding linked CSS for {html_path}: {e}")
            return []

    def extract_style_tag_css(self, html_path):
        """
        Extract CSS from <style> tags in an HTML file.

        Args:
            html_path: Path to the HTML file

        Returns:
            Dictionary mapping style tag index to CSS content
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract style tags content using regex
            style_tags = re.findall(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL)

            # Create a dictionary to store style tag contents
            style_css = {}

            for i, style_content in enumerate(style_tags):
                style_css[f"{html_path}#style{i+1}"] = style_content

            if style_css:
                print(f"Found {len(style_css)} style tag(s) in {html_path}")

            return style_css

        except Exception as e:
            print(f"Error extracting style tags from {html_path}: {e}")
            return {}

    def find_all_css_files(self, folder_path):
        """
        Find all CSS files and maintain a mapping of which CSS files are linked from which HTML files.
        Also extract and include CSS from style tags within HTML files.

        Args:
            folder_path: Path to the folder to search

        Returns:
            Dictionary mapping HTML files to their CSS sources (files and style tags)
        """
        html_files = self.find_html_files(folder_path)
        all_css_files = self.find_css_files(folder_path)

        html_to_css = {}

        for html_file in html_files:
            linked_css = self.find_linked_css_files(html_file, folder_path)
            style_tag_css = self.extract_style_tag_css(html_file)

            # Create temporary files for style tag CSS
            temp_css_files = []
            for style_id, css_content in style_tag_css.items():
                # Create a temporary file path
                style_file_path = os.path.join(self.output_dir, f"temp_{os.path.basename(style_id)}.css")

                # Write the CSS content to the temporary file
                with open(style_file_path, 'w', encoding='utf-8') as f:
                    f.write(css_content)

                temp_css_files.append(style_file_path)

            # Combine linked CSS files and style tag CSS files
            combined_css = linked_css + temp_css_files

            if not combined_css:
                # If no CSS found at all, use all CSS files as fallback
                html_to_css[html_file] = all_css_files
            else:
                html_to_css[html_file] = combined_css

        return html_to_css

    def find_screenshot_pairs(self, screenshot_dir):
        """
        Find matching desktop and mobile screenshot pairs.

        Args:
            screenshot_dir: Directory containing screenshots

        Returns:
            Dictionary mapping base names to (desktop, mobile) screenshot paths
        """
        desktop_screenshots = glob.glob(os.path.join(screenshot_dir, "**", "*.desktop.png"), recursive=True)
        mobile_screenshots = glob.glob(os.path.join(screenshot_dir, "**", "*.mobile.png"), recursive=True)

        # Extract base names (without the .desktop.png or .mobile.png suffix and without the path)
        desktop_bases = {os.path.splitext(os.path.splitext(os.path.basename(path))[0])[0]: path for path in desktop_screenshots}
        mobile_bases = {os.path.splitext(os.path.splitext(os.path.basename(path))[0])[0]: path for path in mobile_screenshots}

        # Find matching pairs
        pairs = {}
        for base in desktop_bases:
            if base in mobile_bases:
                pairs[base] = (desktop_bases[base], mobile_bases[base])

        return pairs

    def match_screenshots_to_html(self, screenshot_pairs, html_files):
        """
        Match screenshot pairs to HTML files based on filename similarity.

        Args:
            screenshot_pairs: Dictionary of screenshot pairs
            html_files: List of HTML file paths

        Returns:
            Dictionary mapping HTML paths to screenshot pairs
        """
        html_to_screenshots = {}

        for html_path in html_files:
            html_base = os.path.splitext(os.path.basename(html_path))[0]

            # Try to find a direct match
            if html_base in screenshot_pairs:
                html_to_screenshots[html_path] = screenshot_pairs[html_base]
                continue

            # If no direct match, find the closest match
            best_match = None
            best_score = 0

            for screenshot_base in screenshot_pairs:
                # Calculate similarity score (simple matching coefficient)
                a = html_base.lower()
                b = screenshot_base.lower()

                # Calculate Levenshtein distance
                distance = 0
                for i in range(min(len(a), len(b))):
                    if a[i] == b[i]:
                        distance += 1

                similarity = distance / max(len(a), len(b))

                if similarity > best_score:
                    best_score = similarity
                    best_match = screenshot_base

            # Use best match if it's reasonably similar
            if best_score > 0.5 and best_match is not None:
                html_to_screenshots[html_path] = screenshot_pairs[best_match]

        return html_to_screenshots

    def analyze_website(self, folder_path, screenshot_dir):
        """
        Analyze the responsiveness of an entire website.

        Args:
            folder_path: Path to the website folder
            screenshot_dir: Directory containing screenshots

        Returns:
            List of page analysis results
        """
        # Step 1: Find all HTML files
        html_files = self.find_html_files(folder_path)
        if not html_files:
            print(f"Warning: No HTML files found in {folder_path}")
            return []

        print(f"Found {len(html_files)} HTML files")

        # Step 2: Find all CSS files and style tags within HTML
        html_to_css = self.find_all_css_files(folder_path)

        # Count total CSS sources (both files and style tags)
        total_css_sources = sum(len(css_files) for css_files in html_to_css.values())
        external_css_count = len(set(css for css_list in html_to_css.values() for css in css_list
                                 if not css.startswith(self.output_dir)))

        print(f"Found {external_css_count} external CSS files and {total_css_sources - external_css_count} style tags")

        # Step 3: Find screenshot pairs
        screenshot_pairs = self.find_screenshot_pairs(screenshot_dir)

        if not screenshot_pairs:
            print(f"Warning: No screenshot pairs found in {screenshot_dir}")
            print("Make sure screenshots follow the naming convention: pagename.desktop.png and pagename.mobile.png")
            return []

        print(f"Found {len(screenshot_pairs)} screenshot pairs")

        # Step 4: Match screenshots to HTML files
        html_to_screenshots = self.match_screenshots_to_html(screenshot_pairs, html_to_css.keys())

        if not html_to_screenshots:
            print("Warning: Could not match any HTML files with screenshot pairs")
            print("Check that HTML filenames correspond to screenshot base names")

            # Print HTML file names and screenshot pair base names for diagnostics
            print("HTML files:")
            for html_file in html_files:
                print(f"  - {os.path.basename(html_file)}")

            print("Screenshot pairs:")
            for base_name in screenshot_pairs:
                print(f"  - {base_name}")

            return []

        print(f"Matched {len(html_to_screenshots)} HTML files with screenshot pairs")

        # Step 5: Analyze each page that has both CSS and screenshots
        results = []

        for html_path, screenshot_pair in html_to_screenshots.items():
            if html_path in html_to_css:
                css_paths = html_to_css[html_path]
                desktop_screenshot, mobile_screenshot = screenshot_pair

                # Check if CSS is from style tags or external files
                style_tag_count = sum(1 for css in css_paths if css.startswith(self.output_dir))
                external_css_count = len(css_paths) - style_tag_count

                css_source = []
                if external_css_count > 0:
                    css_source.append(f"{external_css_count} external CSS file(s)")
                if style_tag_count > 0:
                    css_source.append(f"{style_tag_count} style tag(s)")

                print(f"Analyzing {os.path.basename(html_path)} with {', '.join(css_source)}")

                result = self.analyze_page(html_path, css_paths, desktop_screenshot, mobile_screenshot)
                results.append(result)

        if not results:
            print("Warning: No pages could be analyzed")
            print("Make sure HTML files have linked CSS and matching screenshot pairs")
        else:
            print(f"Successfully analyzed {len(results)} pages")

        # Clean up temporary style tag CSS files
        self._cleanup_temp_files()

        return results

    def _cleanup_temp_files(self):
        """
        Clean up temporary CSS files created from style tags.
        """
        temp_files = glob.glob(os.path.join(self.output_dir, "temp_*.css"))
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Error removing temporary file {temp_file}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze responsive design of a website')
    parser.add_argument('folder', help='Folder containing the website files')
    parser.add_argument('--screenshots', '-s', required=True, help='Directory containing screenshot pairs (.desktop.png and .mobile.png)')
    parser.add_argument('--output', '-o', default='responsive_analysis', help='Output directory for reports')
    parser.add_argument('--format', '-f', choices=['md', 'csv', 'both'], default='both', help='Output format (md, csv, or both)')

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = ResponsiveDesignAnalyzer(args.output)

    # Analyze website
    print(f"Analyzing website in {args.folder}...")
    results = analyzer.analyze_website(args.folder, args.screenshots)
    print(f"Analyzed {len(results)} pages")

    # Generate reports
    if args.format in ['md', 'both']:
        report_path = os.path.join(args.output, 'responsive_analysis.md')
        analyzer.generate_report(results, report_path)
        print(f"Report saved to {report_path}")

    if args.format in ['csv', 'both']:
        csv_path = os.path.join(args.output, 'responsive_analysis.csv')
        analyzer.generate_csv_report(results, csv_path)
        print(f"CSV report saved to {csv_path}")

    print("Responsive design analysis complete!")

