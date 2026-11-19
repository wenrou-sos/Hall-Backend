package logger

import (
    "fmt"
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
    "gopkg.in/natefinch/lumberjack.v2"
    "os"
)

var Service = &service{
    docker:     "/data/log",
    level:      os.Getenv("LOG_LEVEL"),
    serverName: os.Getenv("SERVER_NAME"),
}

type service struct {
    docker     string
    level      string
    serverName string
    Zap        *zap.SugaredLogger
}

func init() {
    Service.startZap()
}

func (s *service) startZap() {
    w := zapcore.AddSync(&lumberjack.Logger{
        Filename:   fmt.Sprintf("%s/%s.log", s.docker, "app"),
        MaxSize:    100, // megabytes
        MaxBackups: 10000,
        MaxAge:     30, // days
    })

    if s.serverName == "" {
        s.serverName = "level"
    }

    c := zapcore.EncoderConfig{
        MessageKey:     "msg",
        LevelKey:       s.serverName,
        TimeKey:        "time",
        NameKey:        "logger",
        CallerKey:      "file",
        StacktraceKey:  "stacktrace",
        LineEnding:     zapcore.DefaultLineEnding,
        EncodeLevel:    zapcore.LowercaseLevelEncoder,
        EncodeTime:     zapcore.ISO8601TimeEncoder,
        EncodeDuration: zapcore.SecondsDurationEncoder,
        EncodeCaller:   zapcore.ShortCallerEncoder,
        EncodeName:     zapcore.FullNameEncoder,
    }

    core := zapcore.NewCore(
        zapcore.NewJSONEncoder(c),
        zapcore.NewMultiWriteSyncer(zapcore.AddSync(os.Stdout), w),
        s.logLevel(),
    )

    logger := zap.New(core, zap.AddCaller(), zap.Development())
    s.Zap = logger.Sugar()
}

func (s *service) logLevel() zapcore.Level {
    switch s.level {
    case "0":
        return zap.DebugLevel

    case "2":
        return zap.WarnLevel

    case "1":
        fallthrough
    default:
        return zap.InfoLevel
    }
}

// implement gorm logger interface
func (s *service) Print(values ...interface{}) {
    s.Zap.Info(values)
}

func (s *service) stopZap() {
    s.Zap.Sync()
}

func (s *service) Destroy() {
    s.stopZap()
}
