const fs = require('fs');
const req = require('request');
const unzipper = require('unzip-stream');
const ffmpeg = require('fluent-ffmpeg');

function getBeatMapSet(curCursor, filter) {
    var info;
    return new Promise((resolve, reject) => {
        // console.log("https://osu.ppy.sh/beatmapsets/search" + filter + curCursor);
        req("https://osu.ppy.sh/beatmapsets/search" + filter + curCursor, (error, response, body) => {
            info = body;
            resolve(info);
        });
    });
};

function dlBeatMap(beatmapset) {
    let id = beatmapset.id;
    return new Promise((resolve, reject) => {
        let path = 'data/' + id + "/";
        // Clean folder first
        fs.readdir(path, (err, files) => {
            if (!err) {
                for (const file of files) {
                    fs.unlink(path + file, err => {
                      if (err) throw err;
                    });
                  }
            }
            
            // Download the beatmap from osu
            req("https://osu.ppy.sh/d/" + id, () => {
                unzipClean(beatmapset);
            }).pipe(fs.createWriteStream(path + id + ".zip"));
        });
        resolve();
    });
};

function unzipClean(beatmapset) {
    let id = beatmapset.id;
    let path = 'data/' + id + "/";
    fs.createReadStream(path + id+ ".zip")
    // Unzip the file
    .pipe(unzipper.Parse())
    .on('entry', function (entry) {
        const fileName = entry.path;
        // Only keep mp3 and osu files
        if (fileName.endsWith(".mp3")) {
            entry.pipe(fs.createWriteStream('data/' + id + "/" + id + ".mp3"));
        }
        else if (fileName.endsWith(".osu")) {
            entry.pipe(fs.createWriteStream('data/' + id + "/" + id + fileName));
        }
        else {
            entry.autodrain();
        }
    })
    .on('close', () => {
        fs.readdir(path, (err, files) => {
            files.forEach((file) => {
                // Delete zip files
                if (file.endsWith(".zip")) {
                    fs.unlink(path + file, (err) => {
                        if (err) throw err;
                    });
                }
                // Convert mp3 files to wav files
                else if (file.endsWith(".mp3")) {
                    mp3towav(path, file);
                }
                // Only keep osumania osu files, e.g. Mode: 3
                else if (file.endsWith(".osu")) {
                    filterOsuManiaFiles(path, file, id);
                }
            })
        })
    });
}

function filterOsuManiaFiles(path, file, id) {
    console.log(path + file + " : " + id);
    fs.readFile(path + file, (err, data) => {
        if (data.indexOf("Mode: 3") < 0) {
            fs.unlink(path + file, (err) => {
                if (err) throw err;
            });
        }
        else {
            // Grab the beatmapId and place the difficulty as part of the file name
            let dataStr = data.toString("utf-8");
            let it = dataStr.indexOf("BeatmapID:") + 10;
            let beatmapId = "";
            while (!isNaN(parseInt(dataStr[it]))) {
                beatmapId += dataStr[it];
                ++it;
            }
            console.log(beatmapId);
            var beatmap = beatmapset.beatmaps.filter((beatmap) => {
                return beatmap.id == beatmapId;
            });

            if (beatmap.length != 1) throw "Found " + beatmap.length + " beatmaps for " + beatmapId;
            beatmap = beatmap[0];

            fs.unlink(path + id + "[" + beatmap.difficulty_rating + "].osu", (err) => {
                fs.renameSync(path + file, path + id + "[" + beatmap.difficulty_rating + "].osu", (err) => {});
            });
        }
    })
}

function mp3towav(path, file) {
    return new Promise((resolve, reject) => {
        let wavFileName = file.replace(".mp3", ".wav");
        ffmpeg(path + file)
        .toFormat('wav')
        .on('error', (err) => {
            console.log('Error occurred on converting mp3 to wav: ' + err.message);
        })
        .on('end', () => {
            fs.unlink(path + file, (err) => {});
        })
        .save(path + wavFileName)
        resolve();
    })
}

async function main() {
    let numData = 10;

    if (process.argv.length > 2) {
        numData = parseInt(process.argv[2]);
        if (isNaN(numData)) throw "Parameter is not a number!";
    }

    console.log("Finding " + numData + " Mania Songs");

    const filter = "?m=3&sort=plays_desc&s=any";
    let curCursor = "";

    var data;
    let max = -1;
    let numFound = 0;
    let numSongs = 0;
    do {
        data = JSON.parse(await getBeatMapSet(curCursor, filter));
        console.log(data.cursor);
        for (beatmapset of data.beatmapsets) {
            if (beatmapset.availability.download_disabled) continue;
            let hasMania = false;
            for (beatmap of beatmapset.beatmaps) {
                if (beatmap.mode_int == 3) {
                    hasMania = true;
                    break;
                }
            }
            if (hasMania) {
                console.log(beatmapset.title + ": " + beatmapset.id + " : " + beatmapset.play_count);
                fs.mkdir('data/' + beatmapset.id, {recursive:true}, (err) =>{});
                await dlBeatMap(beatmapset);
                if (++numFound >= numData) break;
            }
        }
        numSongs += data.beatmapsets.length;
        curCursor = "&cursor%5Bplay_count%5D=" + data.cursor.play_count + "&cursor%5B_id%5D=" + data.cursor._id;

        if (max < 0) {
            max = data.total;
            console.log(max);
        }
    } while (numFound < numData && max > (numSongs));

    console.log("Last Cursor: " + JSON.stringify(data.cursor));
}

main();