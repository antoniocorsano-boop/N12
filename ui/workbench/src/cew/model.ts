import snapshotData from './snapshot.json';

export type DecisionOutcome =
  | 'UNBOUND'
  | 'UNREADABLE'
  | 'NEEDS_BETTER_SOURCE'
  | 'NEEDS_SITE_SURVEY'
  | 'DEFER';

export type RuntimeManifest = {
  schema_version: '1.0';
  stage_status: 'READY' | 'STALE_OR_UNVERIFIED';
  canonical_commit: string;
  archive_commit: string;
  archive_path: string;
  archive_blob_sha: string;
  render_dpi: number;
  render_width_px: number;
  render_height_px: number;
  render_file_sha256: string;
  image_url: string;
  authority: 'DERIVATIVE_REVIEW_CONTEXT_ONLY';
};

export const snapshot = snapshotData;

export function manifestMatchesSnapshot(manifest: RuntimeManifest): boolean {
  const source = snapshot.source;
  return manifest.stage_status === 'READY'
    && manifest.canonical_commit === snapshot.canonical_commit
    && manifest.archive_commit === source.archive_commit
    && manifest.archive_path === source.archive_path
    && manifest.archive_blob_sha === source.archive_blob_sha
    && manifest.render_dpi === source.render.dpi
    && manifest.render_width_px === source.render.width_px
    && manifest.render_height_px === source.render.height_px;
}

export async function loadRuntimeManifest(): Promise<RuntimeManifest | null> {
  try {
    const response = await fetch('./runtime/tav06a-p001.manifest.json', {
      method: 'GET',
      cache: 'no-store'
    });
    if (!response.ok) return null;
    return (await response.json()) as RuntimeManifest;
  } catch {
    return null;
  }
}
