package vn.edu.library.util;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;

public final class DateUtil {
    public static final String PATTERN = "dd/MM/yyyy";

    private DateUtil() {
    }

    public static Date parse(String value) {
        try {
            return new SimpleDateFormat(PATTERN).parse(value);
        } catch (ParseException e) {
            return null;
        }
    }

    public static String format(Date value) {
        if (value == null) {
            return "";
        }
        return new SimpleDateFormat(PATTERN).format(value);
    }

    public static Date addDays(Date value, int days) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(value);
        calendar.add(Calendar.DAY_OF_MONTH, days);
        return calendar.getTime();
    }

    public static long daysBetween(Date start, Date end) {
        long millis = end.getTime() - start.getTime();
        return millis / (24 * 60 * 60 * 1000);
    }
}
