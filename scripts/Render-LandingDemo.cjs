// Build the scroll reel and its motion-free plates from actual workspace captures.
// Usage: node scripts/Render-LandingDemo.cjs <directory of 1440 x 940 valor-product-*.png captures>
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const captures = path.resolve(process.argv[2] || "artifacts");
const output = path.resolve(__dirname, "../src/aace/demo/static");
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "valor-reel-"));
const source = view => path.join(captures, "valor-product-" + view + ".png");
const asset = name => path.join(output, "landing-" + name);
const ffmpeg = args => execFileSync("ffmpeg", ["-hide_banner", "-loglevel", "error", "-y", ...args], { cwd: temporary });

// The same decision is selected in each capture. Frame the actual inspection surface.
const scenes = [
  { view: "overview", x: 241, y: 357, w: 796, h: 398 },
  { view: "evaluations", x: 244, y: 395, w: 1152, h: 576 },
  { view: "runs", x: 887, y: 369, w: 530, h: 265 },
  { view: "evidence", x: 244, y: 367, w: 700, h: 350 },
];

try {
  ffmpeg(["-i", source("overview"), "-vf", "crop=1424:910:0:0", "-quality", "91", asset("hero.webp")]);
  const plates = [];
  for (const [index, s] of scenes.entries()) {
    const input = source(s.view);
    const plate = path.join(temporary, index + ".png");
    // Clamp the capture to its real viewport before scaling.
    const crop = `crop=${s.w}:${s.h}:${s.x}:${s.y},scale=1120:560:flags=lanczos,setsar=1`;
    ffmpeg(["-i", input, "-vf", crop, "-frames:v", "1", plate]);
    plates.push(plate);
    // A small optical push keeps the recorded interface legible during a scroll.
    const motion = "scale=2240:1120,zoompan=z='1+0.035*on/71':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=72:s=1120x560:fps=24";
    ffmpeg(["-i", plate, "-vf", motion, "-frames:v", "72", "-c:v", "libvpx-vp9",
      "-threads", "4", "-row-mt", "1", "-cpu-used", "5", "-crf", "22", "-b:v", "0",
      "-pix_fmt", "yuv420p", "-g", "6", path.join(temporary, index + ".webm")]);
  }
  ffmpeg([...plates.flatMap(p => ["-i", p]), "-filter_complex", "vstack=inputs=4", "-frames:v", "1", "-quality", "93", asset("preview.webp")]);
  const manifest = path.join(temporary, "shots.txt");
  fs.writeFileSync(manifest, scenes.map((_, i) => "file '" + i + ".webm'").join("\n"));
  ffmpeg(["-f", "concat", "-safe", "1", "-i", "shots.txt", "-c", "copy", asset("demo.webm")]);
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
